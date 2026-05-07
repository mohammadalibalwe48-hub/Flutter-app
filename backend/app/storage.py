"""On-disk job tracker. Single-process; jobs are kept in memory plus a marker
file so completed builds survive process restarts and can be re-served.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .config import settings
from .models import BuildDetail, BuildState, BuildSummary

_lock = threading.Lock()
_jobs: dict[str, BuildJob] = {}


def _now() -> datetime:
    return datetime.now(UTC)


class BuildJob:
    """A single build's mutable state. Mutations go through ``update``."""

    def __init__(
        self,
        *,
        source_label: str,
        github_url: str | None = None,
        branch: str | None = None,
        project_subdir: str | None = None,
        zip_path: Path | None = None,
    ) -> None:
        self.id: str = uuid.uuid4().hex[:12]
        self.state: BuildState = "queued"
        self.source_label = source_label
        self.github_url = github_url
        self.branch = branch
        self.project_subdir = project_subdir
        self.zip_path = zip_path
        self.logs: str = ""
        self.error: str | None = None
        self.created_at = _now()
        self.updated_at = self.created_at
        self.work_dir: Path = settings.artifacts_dir / self.id
        self.work_dir.mkdir(parents=True, exist_ok=True)

    @property
    def src_dir(self) -> Path:
        return self.work_dir / "src"

    @property
    def web_dir(self) -> Path:
        return self.work_dir / "web"

    @property
    def is_terminal(self) -> bool:
        return self.state in ("ready", "failed", "cancelled")

    def append_log(self, line: str) -> None:
        with _lock:
            self.logs += line if line.endswith("\n") else line + "\n"
            self.updated_at = _now()
            self._persist()

    def update(
        self,
        *,
        state: BuildState | None = None,
        error: str | None = None,
    ) -> None:
        with _lock:
            if state is not None:
                self.state = state
            if error is not None:
                self.error = error
            self.updated_at = _now()
            self._persist()

    def to_summary(self) -> BuildSummary:
        return BuildSummary(
            id=self.id,
            state=self.state,
            source_label=self.source_label,
            created_at=self.created_at,
            updated_at=self.updated_at,
            preview_url=self._preview_url(),
            error=self.error,
        )

    def to_detail(self) -> BuildDetail:
        return BuildDetail(
            id=self.id,
            state=self.state,
            source_label=self.source_label,
            created_at=self.created_at,
            updated_at=self.updated_at,
            preview_url=self._preview_url(),
            error=self.error,
            logs=self.logs,
            project_subdir=self.project_subdir,
        )

    def _preview_url(self) -> str | None:
        if self.state != "ready":
            return None
        base = settings.public_origin.rstrip("/") if settings.public_origin else ""
        return f"{base}/preview/{self.id}/"

    def _persist(self) -> None:
        marker = self.work_dir / "job.json"
        marker.write_text(
            json.dumps(
                {
                    "id": self.id,
                    "state": self.state,
                    "source_label": self.source_label,
                    "github_url": self.github_url,
                    "branch": self.branch,
                    "project_subdir": self.project_subdir,
                    "error": self.error,
                    "created_at": self.created_at.isoformat(),
                    "updated_at": self.updated_at.isoformat(),
                }
            )
        )


def create_job(**kwargs: object) -> BuildJob:
    job = BuildJob(**kwargs)  # type: ignore[arg-type]
    with _lock:
        _jobs[job.id] = job
    job.update(state="queued")
    return job


def get_job(job_id: str) -> BuildJob | None:
    with _lock:
        job = _jobs.get(job_id)
    if job is not None:
        return job
    # Try to rehydrate from disk so previously-built jobs still serve.
    marker = settings.artifacts_dir / job_id / "job.json"
    if not marker.is_file():
        return None
    data = json.loads(marker.read_text())
    rehydrated = BuildJob(
        source_label=data["source_label"],
        github_url=data.get("github_url"),
        branch=data.get("branch"),
        project_subdir=data.get("project_subdir"),
    )
    rehydrated.id = data["id"]
    rehydrated.state = data["state"]
    rehydrated.error = data.get("error")
    rehydrated.created_at = datetime.fromisoformat(data["created_at"])
    rehydrated.updated_at = datetime.fromisoformat(data["updated_at"])
    rehydrated.work_dir = settings.artifacts_dir / rehydrated.id
    log_file = rehydrated.work_dir / "build.log"
    if log_file.is_file():
        rehydrated.logs = log_file.read_text(errors="replace")
    with _lock:
        _jobs[rehydrated.id] = rehydrated
    return rehydrated


def list_jobs(limit: int = 50) -> list[BuildSummary]:
    with _lock:
        jobs = sorted(_jobs.values(), key=lambda j: j.created_at, reverse=True)
    return [j.to_summary() for j in jobs[:limit]]
