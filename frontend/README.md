# Flutter Tester — Frontend

Single-page React/Vite app that talks to the backend FastAPI service to build and
preview any Flutter app in the browser.

## Local development

```bash
cd frontend
npm install
npm run dev
```

The app reads the backend URL and shared token from `localStorage` (set them
via the in-app **Settings** dialog).

For a baked-in default backend URL, set `VITE_BACKEND_URL` at build time:

```bash
VITE_BACKEND_URL=https://flutter-tester.fly.dev npm run build
```

## Deployment

Designed for `deploy frontend` on devinapps.com after `npm run build`.
