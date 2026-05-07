# Hugging Face Spaces variant of the Flutter Tester backend.
#
# Differences vs. backend/Dockerfile (which targets Fly.io):
#   - Uses UID 1000 (HF Spaces convention) instead of 10001.
#   - No persistent volume / gosu entrypoint (HF Spaces is ephemeral).
#   - Default data directory lives under the user home so the runtime can
#     write to it without privilege escalation.

FROM ghcr.io/cirruslabs/flutter:3.41.9 AS flutter-sdk
RUN flutter precache --web --no-android --no-ios --no-linux --no-macos --no-windows \
 && flutter --disable-analytics

FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:/home/user/.local/bin:${PATH}" \
    FLUTTER_BIN=/opt/flutter/bin/flutter \
    FLUTTER_TESTER_DATA_DIR=/home/user/data \
    HOME=/home/user

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        git curl ca-certificates xz-utils \
 && rm -rf /var/lib/apt/lists/*

COPY --from=flutter-sdk /sdks/flutter /opt/flutter
RUN git config --system --add safe.directory /opt/flutter

RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "pydantic>=2.7.0" \
    "python-multipart>=0.0.9" \
    "httpx>=0.27.0"

# HF Spaces convention: user named `user` with UID 1000.
RUN useradd -m -u 1000 user \
 && mkdir -p /home/user/data \
 && chown -R user:user /opt/flutter /home/user

WORKDIR /home/user/app
COPY --chown=user:user app /home/user/app/app
COPY --chown=user:user static /home/user/app/static
COPY --chown=user:user pyproject.toml /home/user/app/pyproject.toml

USER user

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
