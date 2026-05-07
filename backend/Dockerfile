# Custom image baking in Flutter SDK + FastAPI runtime.
#
# Stage 1: pull the Flutter SDK from a maintained image and pre-warm web tooling.
FROM ghcr.io/cirruslabs/flutter:3.41.9 AS flutter-sdk
RUN flutter precache --web --no-android --no-ios --no-linux --no-macos --no-windows \
 && flutter --disable-analytics

# Stage 2: small Python runtime that copies the SDK in.
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:${PATH}" \
    FLUTTER_BIN=/opt/flutter/bin/flutter \
    FLUTTER_TESTER_DATA_DIR=/data

# Build deps for git, plus libs that Flutter web tooling occasionally needs.
# `gosu` lets the entrypoint drop privileges from root to the app user.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        git curl ca-certificates xz-utils gosu \
 && rm -rf /var/lib/apt/lists/*

# Pull the SDK into the runtime image.
COPY --from=flutter-sdk /sdks/flutter /opt/flutter
RUN git config --global --add safe.directory /opt/flutter

# Pre-install Python deps as root so they land in the system site-packages.
WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "pydantic>=2.7.0" \
    "python-multipart>=0.0.9" \
    "httpx>=0.27.0"

# Run as non-root for safety; Flutter complains otherwise.
RUN useradd -m -u 10001 app && chown -R app:app /opt/flutter /app

COPY --chown=app:app app /app/app
# Optional: prebuilt frontend bundle is mounted alongside the backend so the
# whole tester is one same-origin service. The build is reproducible from
# `frontend/`; see frontend/README.md.
COPY --chown=app:app static /app/static
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Persistent data volume (artifacts + cached SDK fallback).
VOLUME ["/data"]
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
