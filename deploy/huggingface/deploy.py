#!/usr/bin/env python3
"""Deploy the Flutter Tester to a Hugging Face Space (Docker SDK).

Prereqs:
  - `pip install huggingface_hub`
  - `cd frontend && npm install && npm run build`  (produces frontend/dist)
  - export HF_TOKEN=<write-scoped HF access token>
  - export HF_USERNAME=<your HF username>          (defaults to whoami())
  - export FLUTTER_TESTER_TOKEN=<long random string for the X-Tester-Token header>

Usage:
  python3 deploy/huggingface/deploy.py [--space-name flutter-tester]

What this does:
  1. Creates (or reuses) the HF Space `<username>/<space-name>` with sdk=docker.
  2. Sets `FLUTTER_TESTER_TOKEN` as a Space secret (re-runs of the script
     overwrite the value).
  3. Stages the deployment files (Dockerfile, README.md frontmatter, backend/app,
     backend/pyproject.toml, frontend/dist as `static/`) into a temp directory.
  4. Uploads the staged folder to the Space and triggers a build.

After upload, watch the build at:
  https://huggingface.co/spaces/<username>/<space-name>
The Space goes live at:
  https://<username-lowercased>-<space-name>.hf.space/
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi


def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        sys.exit(f"error: ${name} is required (see header docstring)")
    return val


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--space-name", default="flutter-tester")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="path to the Flutter-app git checkout root",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    here = Path(__file__).resolve().parent

    token = _require_env("HF_TOKEN")
    tester_token = _require_env("FLUTTER_TESTER_TOKEN")

    api = HfApi(token=token)
    username = os.environ.get("HF_USERNAME") or api.whoami()["name"]
    repo_id = f"{username}/{args.space_name}"

    print(f"[deploy] Creating Space {repo_id} (sdk=docker, exist_ok=True)...")
    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="docker",
        exist_ok=True,
        private=False,
    )

    print("[deploy] Setting FLUTTER_TESTER_TOKEN as a Space secret...")
    api.add_space_secret(
        repo_id=repo_id,
        key="FLUTTER_TESTER_TOKEN",
        value=tester_token,
        description="Shared secret required by /api/* endpoints.",
    )

    backend = repo_root / "backend"
    frontend_dist = repo_root / "frontend" / "dist"
    if not frontend_dist.is_dir():
        sys.exit(
            "error: frontend/dist not found. Run `cd frontend && npm install && npm run build` first."
        )

    with tempfile.TemporaryDirectory() as td:
        staging = Path(td)
        shutil.copytree(backend / "app", staging / "app")
        shutil.copy(backend / "pyproject.toml", staging / "pyproject.toml")
        shutil.copytree(frontend_dist, staging / "static")
        shutil.copy(here / "Dockerfile", staging / "Dockerfile")
        shutil.copy(here / "README.md", staging / "README.md")

        print(f"[deploy] Uploading staged folder: {staging}")
        commit = api.upload_folder(
            repo_id=repo_id,
            repo_type="space",
            folder_path=str(staging),
            commit_message="Deploy flutter-tester (backend + frontend bundle)",
        )
        print(f"[deploy] Commit: {commit}")

    print(
        f"[deploy] Done. Watch build: https://huggingface.co/spaces/{repo_id}\n"
        f"[deploy] Live URL once ready: https://{username.lower()}-{args.space_name}.hf.space/"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
