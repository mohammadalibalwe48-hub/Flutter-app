# Flutter Tester — Backend

FastAPI service that takes a public GitHub repo URL or a `.zip` upload of a
Flutter project, runs `flutter build web --release`, and serves the resulting
single-page app under `/preview/<job_id>/`.

## Endpoints

| Method | Path                           | Auth | Description                                      |
| ------ | ------------------------------ | ---- | ------------------------------------------------ |
| GET    | `/healthz`                     | no   | Liveness probe.                                   |
| POST   | `/api/builds`                  | yes  | Submit a GitHub URL.                              |
| POST   | `/api/builds/upload`           | yes  | Submit a `.zip` of a Flutter project.             |
| GET    | `/api/builds`                  | yes  | List recent builds.                               |
| GET    | `/api/builds/{id}`             | yes  | Build status + logs.                              |
| GET    | `/preview/{id}/...`            | no   | Serves the built Flutter Web app for that build.  |

Auth is a single shared secret in the `X-Tester-Token` header. Configure it on
the server with `FLUTTER_TESTER_TOKEN`.

## Local development

```bash
cd backend
uv sync             # or: pip install -e .[dev]
export FLUTTER_TESTER_TOKEN=local-dev-secret
export FLUTTER_TESTER_DATA_DIR=$PWD/data
uvicorn app.main:app --reload --port 8080
```

The server will install Flutter on first build into `$FLUTTER_TESTER_DATA_DIR/flutter`
unless `FLUTTER_BIN` is set.

## Docker

```bash
docker build -t flutter-tester-backend .
docker run --rm -p 8080:8080 \
  -e FLUTTER_TESTER_TOKEN=local-dev-secret \
  -v $PWD/data:/data \
  flutter-tester-backend
```

## Deployment

Designed for `deploy backend` on Fly.io with a persistent volume. See
`Dockerfile` and `fly.toml` for the production config.
