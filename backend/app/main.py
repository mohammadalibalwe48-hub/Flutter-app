from __future__ import annotations

import logging
import mimetypes
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from .api.builds import router as builds_router
from .config import settings
from .worker import start_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    log.info("data_dir=%s artifacts_dir=%s", settings.data_dir, settings.artifacts_dir)
    await start_worker()
    yield


app = FastAPI(
    title="Flutter Tester",
    description="Build any Flutter project from a GitHub URL or zip and run it in a browser.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(builds_router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/preview/{job_id}")
@app.get("/preview/{job_id}/")
@app.get("/preview/{job_id}/{path:path}")
async def serve_preview(job_id: str, path: str = "") -> Response:
    """Serve a built Flutter Web app from artifacts_dir/<id>/web/.

    Note: this endpoint is intentionally unauthenticated so the iframe can load
    without sending custom headers. Knowing a job_id is required.
    """
    web_root = (settings.artifacts_dir / job_id / "web").resolve()
    if not web_root.is_dir():
        raise HTTPException(status_code=404, detail="Build not ready or unknown job.")
    if not path:
        path = "index.html"
    target = (web_root / path).resolve()
    # Prevent escape outside the build's web/ directory.
    if not str(target).startswith(str(web_root) + "/") and target != web_root:
        raise HTTPException(status_code=403, detail="Forbidden")
    if target.is_dir():
        target = target / "index.html"
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    media_type, _ = mimetypes.guess_type(str(target))
    return FileResponse(target, media_type=media_type or "application/octet-stream")


# Serve the frontend SPA from the same origin. Bundle is mounted at /ui/* and
# the / route redirects there. Keeping the SPA same-origin avoids cross-origin
# auth + CORS headaches when the backend is behind a basic-auth tunnel.
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/")
async def root() -> Response:
    index = _FRONTEND_DIR / "index.html"
    if index.is_file():
        return FileResponse(index, media_type="text/html")
    return Response(
        content="Flutter Tester backend is running. Build the frontend into backend/static/.",
        media_type="text/plain",
    )


@app.get("/{path:path}")
async def serve_frontend(path: str) -> Response:
    if not _FRONTEND_DIR.is_dir():
        raise HTTPException(status_code=404, detail="Frontend bundle not present")
    candidate = (_FRONTEND_DIR / path).resolve()
    if str(candidate).startswith(str(_FRONTEND_DIR.resolve())) and candidate.is_file():
        media_type, _ = mimetypes.guess_type(str(candidate))
        return FileResponse(candidate, media_type=media_type or "application/octet-stream")
    # SPA fallback: serve index.html for unknown paths so client-side routes work.
    index = _FRONTEND_DIR / "index.html"
    if index.is_file():
        return FileResponse(index, media_type="text/html")
    raise HTTPException(status_code=404, detail="Not found")
