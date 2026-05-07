from __future__ import annotations

import os
from pathlib import Path


class Settings:
    """Runtime configuration. All values come from environment variables."""

    # Where built artifacts and cloned sources live. On Fly.io this is mounted
    # from a persistent volume so artifacts survive restarts.
    data_dir: Path = Path(os.environ.get("FLUTTER_TESTER_DATA_DIR", "/data"))

    # Shared secret required on every /api/* request. Frontend stores it once
    # in localStorage and sends it in the X-Tester-Token header.
    api_token: str = os.environ.get("FLUTTER_TESTER_TOKEN", "")

    # Where to find the Flutter SDK. If FLUTTER_BIN is set we trust it; otherwise
    # we install the SDK at runtime under data_dir/flutter (slow first boot).
    flutter_bin_env: str | None = os.environ.get("FLUTTER_BIN")

    # Public origin for serving preview iframes (e.g. https://flutter-tester.fly.dev).
    # When unset, links use a relative path.
    public_origin: str = os.environ.get("FLUTTER_TESTER_PUBLIC_ORIGIN", "")

    # CORS allow-list for the frontend.
    cors_origins: list[str] = [
        o.strip()
        for o in os.environ.get(
            "FLUTTER_TESTER_CORS_ORIGINS",
            "http://localhost:5173,http://localhost:4173",
        ).split(",")
        if o.strip()
    ]

    # Caps.
    max_zip_bytes: int = int(os.environ.get("FLUTTER_TESTER_MAX_ZIP_MB", "50")) * 1024 * 1024
    build_timeout_sec: int = int(os.environ.get("FLUTTER_TESTER_BUILD_TIMEOUT_SEC", "600"))
    artifact_ttl_hours: int = int(os.environ.get("FLUTTER_TESTER_ARTIFACT_TTL_HOURS", "24"))
    max_concurrent_builds: int = int(os.environ.get("FLUTTER_TESTER_MAX_CONCURRENT", "1"))

    @property
    def artifacts_dir(self) -> Path:
        return self.data_dir / "artifacts"

    @property
    def sdk_dir(self) -> Path:
        return self.data_dir / "flutter"


settings = Settings()
