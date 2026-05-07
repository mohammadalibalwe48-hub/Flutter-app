from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from ..auth import require_token
from ..config import settings
from ..models import BuildDetail, BuildSummary, GithubBuildRequest
from ..storage import create_job, get_job, list_jobs
from ..worker import GITHUB_URL_RE, queue_build

router = APIRouter(prefix="/api/builds", tags=["builds"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_token)],
)
async def create_build_from_github(req: GithubBuildRequest) -> BuildSummary:
    """Submit a GitHub URL for building."""
    url = str(req.github_url).rstrip("/")
    if not GITHUB_URL_RE.match(url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only public github.com URLs are supported.",
        )
    job = create_job(
        source_label=url,
        github_url=url,
        branch=req.branch,
        project_subdir=req.project_subdir,
    )
    queue_build(job)
    return job.to_summary()


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_token)],
)
async def create_build_from_zip(
    file: UploadFile = File(...),
    project_subdir: str | None = Form(default=None),
) -> BuildSummary:
    """Submit a .zip of a Flutter project for building."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Upload must be a .zip file.")
    # Stream the upload to disk while enforcing the size cap.
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = settings.artifacts_dir / f"upload-{file.filename}"
    total = 0
    with tmp_path.open("wb") as out:
        while True:
            chunk = await file.read(1 << 20)
            if not chunk:
                break
            total += len(chunk)
            if total > settings.max_zip_bytes:
                tmp_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Upload exceeds size limit.")
            out.write(chunk)
    job = create_job(
        source_label=file.filename,
        project_subdir=project_subdir,
        zip_path=Path(tmp_path),
    )
    # Move the upload into the job's workdir so cleanup is easy.
    final_zip = job.work_dir / "upload.zip"
    tmp_path.rename(final_zip)
    job.zip_path = final_zip
    queue_build(job)
    return job.to_summary()


@router.get("", dependencies=[Depends(require_token)])
async def list_builds() -> list[BuildSummary]:
    return list_jobs()


@router.get("/{job_id}", dependencies=[Depends(require_token)])
async def get_build(job_id: str) -> BuildDetail:
    job = get_job(job_id)
    if job is None:
        return JSONResponse(  # type: ignore[return-value]
            status_code=404,
            content={"detail": "Not found"},
        )
    return job.to_detail()
