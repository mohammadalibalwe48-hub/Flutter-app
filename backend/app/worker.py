"""Background build worker.

Single-tenant for v1: at most ``max_concurrent_builds`` builds run in parallel.
Each job is processed by ``run_build``, which streams subprocess output back
into the job's log buffer.
"""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
import zipfile
from pathlib import Path

from .config import settings
from .sdk import ensure_flutter
from .storage import BuildJob

log = logging.getLogger(__name__)

_queue: asyncio.Queue[BuildJob] | None = None
_workers_started = False
GITHUB_URL_RE = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+(\.git)?/?$")


def queue_build(job: BuildJob) -> None:
    """Enqueue a job for the worker pool. Must be called after ``start_worker``."""
    if _queue is None:
        raise RuntimeError("Worker not started")
    _queue.put_nowait(job)


async def start_worker() -> None:
    """Spin up the background worker tasks. Idempotent."""
    global _queue, _workers_started
    if _workers_started:
        return
    _queue = asyncio.Queue()
    for _ in range(settings.max_concurrent_builds):
        asyncio.create_task(_worker_loop())
    _workers_started = True


async def _worker_loop() -> None:
    assert _queue is not None
    while True:
        job = await _queue.get()
        try:
            await asyncio.wait_for(run_build(job), timeout=settings.build_timeout_sec)
        except TimeoutError:
            job.append_log(f"\n[timeout after {settings.build_timeout_sec}s]\n")
            job.update(state="failed", error="Build timed out")
        except Exception as exc:  # noqa: BLE001
            log.exception("Build %s crashed", job.id)
            job.append_log(f"\n[internal error] {exc!r}\n")
            job.update(state="failed", error=f"Internal error: {exc!r}")
        finally:
            _queue.task_done()


async def run_build(job: BuildJob) -> None:
    """Execute one build job through all stages."""
    job.update(state="preparing")
    job.append_log(f"=== build {job.id} started ===")

    try:
        flutter_bin = await ensure_flutter()
    except Exception as exc:  # noqa: BLE001
        job.append_log(f"[fatal] Flutter SDK install failed: {exc!r}")
        job.update(state="failed", error="Flutter SDK install failed")
        return

    job.append_log(f"flutter: {flutter_bin}")

    # 1. Materialize source tree.
    if job.zip_path is not None:
        await _extract_zip(job, job.zip_path)
    elif job.github_url is not None:
        await _git_clone(job, job.github_url, job.branch)
    else:
        job.update(state="failed", error="No source provided")
        return

    project_dir = job.src_dir
    if job.project_subdir:
        project_dir = (job.src_dir / job.project_subdir).resolve()
        if not str(project_dir).startswith(str(job.src_dir.resolve())):
            job.update(state="failed", error="Invalid project_subdir (path traversal)")
            return
    if not (project_dir / "pubspec.yaml").is_file():
        job.append_log(f"[error] pubspec.yaml not found in {project_dir}")
        job.update(state="failed", error="No pubspec.yaml at project root")
        return

    # 2. flutter pub get
    job.update(state="installing")
    rc = await _stream_command(
        job,
        [str(flutter_bin), "pub", "get"],
        cwd=project_dir,
    )
    if rc != 0:
        job.update(state="failed", error="flutter pub get failed")
        return

    # 3. flutter build web
    job.update(state="building")
    base_href = f"/preview/{job.id}/"
    rc = await _stream_command(
        job,
        [
            str(flutter_bin),
            "build",
            "web",
            "--release",
            f"--base-href={base_href}",
        ],
        cwd=project_dir,
    )
    if rc != 0:
        job.update(state="failed", error="flutter build web failed")
        return

    # 4. Publish artifacts.
    web_src = project_dir / "build" / "web"
    if not web_src.is_dir():
        job.update(state="failed", error="build/web missing after successful build")
        return
    if job.web_dir.exists():
        shutil.rmtree(job.web_dir)
    shutil.copytree(web_src, job.web_dir)
    job.append_log(f"published {sum(1 for _ in job.web_dir.rglob('*'))} files to {job.web_dir}")

    # 5. Free the source tree to save disk; the user only needs the built web/.
    shutil.rmtree(job.src_dir, ignore_errors=True)

    job.update(state="ready")
    job.append_log("=== build complete ===")


async def _git_clone(job: BuildJob, url: str, branch: str | None) -> None:
    if not GITHUB_URL_RE.match(url):
        raise ValueError(f"Refusing non-github URL: {url}")
    if job.src_dir.exists():
        shutil.rmtree(job.src_dir)
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd += ["--branch", branch]
    cmd += [url, str(job.src_dir)]
    rc = await _stream_command(job, cmd, cwd=job.work_dir)
    if rc != 0:
        raise RuntimeError("git clone failed")


async def _extract_zip(job: BuildJob, zip_path: Path) -> None:
    if job.src_dir.exists():
        shutil.rmtree(job.src_dir)
    job.src_dir.mkdir(parents=True, exist_ok=True)
    job.append_log(f"extracting {zip_path.name}")
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            # Path-traversal guard.
            target = (job.src_dir / member.filename).resolve()
            if not str(target).startswith(str(job.src_dir.resolve())):
                raise RuntimeError(f"Refusing zip entry outside dir: {member.filename}")
        zf.extractall(job.src_dir)
    # If the zip contained a single top-level directory, hoist its contents up.
    entries = [p for p in job.src_dir.iterdir() if p.name not in {"__MACOSX"}]
    if len(entries) == 1 and entries[0].is_dir():
        only = entries[0]
        for child in list(only.iterdir()):
            shutil.move(str(child), str(job.src_dir / child.name))
        shutil.rmtree(only, ignore_errors=True)
    zip_path.unlink(missing_ok=True)


async def _stream_command(
    job: BuildJob,
    cmd: list[str],
    *,
    cwd: Path,
) -> int:
    job.append_log(f"$ {' '.join(cmd)}")
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    assert proc.stdout is not None
    log_file = job.work_dir / "build.log"
    with log_file.open("ab") as raw_log:
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            raw_log.write(line)
            try:
                job.append_log(line.decode(errors="replace").rstrip("\n"))
            except Exception:  # noqa: BLE001
                job.append_log("[binary log line]")
    rc = await proc.wait()
    job.append_log(f"[exit {rc}]")
    return rc
