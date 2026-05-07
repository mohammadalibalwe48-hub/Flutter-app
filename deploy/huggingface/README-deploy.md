# Deploy Flutter Tester to Hugging Face Spaces

A free, no-credit-card hosting option for the Flutter Tester. The Space runs
the full stack (FastAPI + Flutter SDK + frontend bundle) inside a single
Docker container and is reachable at `https://<username>-<space>.hf.space`.

## One-time setup

1. Sign up at <https://huggingface.co/join>.
2. Create a write-scoped access token at
   <https://huggingface.co/settings/tokens> (role: Write).
3. Build the frontend bundle once so it can be baked into the image:

   ```bash
   cd frontend
   npm install
   npm run build   # produces frontend/dist
   ```

4. Pick a long random string for the tester token. Anyone who knows this
   token can submit builds, so don't reuse passwords.

## Deploy

```bash
pip install huggingface_hub
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export FLUTTER_TESTER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"

python3 deploy/huggingface/deploy.py --space-name flutter-tester
```

Re-running the script reuses the Space, refreshes the secret, and pushes a
new commit (which triggers a rebuild).

## After deploy

1. Open `https://huggingface.co/spaces/<username>/flutter-tester` and wait for
   the build to finish (~3–6 min on first deploy, ~30s on subsequent
   deploys thanks to layer caching).
2. Open `https://<username-lowercase>-flutter-tester.hf.space/`.
3. The Settings dialog will prompt for the tester token — paste the value of
   `FLUTTER_TESTER_TOKEN` you generated above. The Backend URL field can be
   left blank (the SPA falls back to same-origin).
4. Submit a public Flutter repo URL (e.g. `https://github.com/flutter/codelabs`
   with subdir `namer/step_07_d_use_selectedindex`) to confirm the pipeline.

## Caveats

- HF Spaces free tier has ephemeral storage — artifacts may be lost when the
  Space restarts. Each build is reproducible from the source repo.
- Free Spaces also sleep after extended inactivity; the first request after a
  sleep takes ~30s to spin back up.
- Native-only Flutter plugins (camera, BLE, etc.) won't run because the build
  target is `flutter build web`.
