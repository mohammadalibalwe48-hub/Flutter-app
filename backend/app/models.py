from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

BuildState = Literal[
    "queued",
    "preparing",  # cloning repo or extracting zip
    "installing",  # flutter pub get
    "building",  # flutter build web
    "ready",
    "failed",
    "cancelled",
]


class GithubBuildRequest(BaseModel):
    """JSON body for POST /api/builds when using a GitHub URL."""

    github_url: HttpUrl
    branch: str | None = None
    project_subdir: str | None = Field(
        default=None,
        description="Path inside the repo to the directory containing pubspec.yaml.",
    )


class BuildSummary(BaseModel):
    id: str
    state: BuildState
    source_label: str  # human-readable (repo URL or filename)
    created_at: datetime
    updated_at: datetime
    preview_url: str | None = None
    error: str | None = None


class BuildDetail(BuildSummary):
    logs: str
    project_subdir: str | None = None
