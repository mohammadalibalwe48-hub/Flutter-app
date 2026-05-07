"""Locate (and if necessary install) the Flutter SDK at runtime.

When the deploy environment provides the SDK at build time (custom Dockerfile),
``FLUTTER_BIN`` is set and we just use it. Otherwise we lazily download a
pinned Flutter release into the data volume on first use. Subsequent boots
reuse the cached SDK.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import tarfile
from pathlib import Path

import httpx

from .config import settings

log = logging.getLogger(__name__)

# Pinned to a recent stable release. Bump as needed.
FLUTTER_VERSION = "3.41.9"
FLUTTER_TARBALL_URL = (
    f"https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/"
    f"flutter_linux_{FLUTTER_VERSION}-stable.tar.xz"
)

_install_lock = asyncio.Lock()


async def ensure_flutter() -> Path:
    """Return a path to the ``flutter`` executable, installing if needed."""
    if settings.flutter_bin_env:
        bin_path = Path(settings.flutter_bin_env)
        if bin_path.is_file():
            return bin_path

    bin_path = settings.sdk_dir / "bin" / "flutter"
    if bin_path.is_file():
        return bin_path

    async with _install_lock:
        if bin_path.is_file():
            return bin_path
        await _download_and_extract()
        if not bin_path.is_file():
            raise RuntimeError(f"Flutter install failed: {bin_path} missing after extract.")
        await _precache_web(bin_path)
        return bin_path


async def _download_and_extract() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    tmp = settings.data_dir / "flutter.tar.xz"
    log.info("Downloading Flutter SDK %s", FLUTTER_VERSION)
    async with httpx.AsyncClient(timeout=httpx.Timeout(600)) as client:
        async with client.stream("GET", FLUTTER_TARBALL_URL) as resp:
            resp.raise_for_status()
            with tmp.open("wb") as f:
                async for chunk in resp.aiter_bytes(chunk_size=1 << 20):
                    f.write(chunk)
    log.info("Extracting Flutter SDK to %s", settings.sdk_dir)
    if settings.sdk_dir.exists():
        shutil.rmtree(settings.sdk_dir)
    # The tarball extracts into a top-level "flutter/" directory; we extract into data_dir.
    with tarfile.open(tmp, mode="r:xz") as tf:
        tf.extractall(path=settings.data_dir)
    tmp.unlink(missing_ok=True)


async def _precache_web(flutter_bin: Path) -> None:
    """Pre-download web build assets so the first user build is faster."""
    log.info("Precaching Flutter web tooling")
    proc = await asyncio.create_subprocess_exec(
        str(flutter_bin),
        "precache",
        "--web",
        "--no-android",
        "--no-ios",
        "--no-linux",
        "--no-macos",
        "--no-windows",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    await proc.wait()
