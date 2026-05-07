---
title: Flutter Tester
emoji: 🐦
colorFrom: blue
colorTo: pink
sdk: docker
app_port: 8080
pinned: false
short_description: Build any Flutter app from a GitHub URL or zip.
---

# Flutter Tester

Submit a public GitHub repository URL (with optional branch and project subdirectory)
or upload a zipped Flutter project. The backend runs `flutter build web --release`
and serves the build as an interactive iframe with phone / tablet / desktop frames.

## How to use

1. Open this Space in a browser.
2. The first time, it asks for a tester token. Paste the value of the
   `FLUTTER_TESTER_TOKEN` secret configured on this Space.
3. Submit a Flutter repo URL (e.g. `https://github.com/flutter/codelabs` with
   subdir `namer/step_07_d_use_selectedindex`) and watch the build run.

## Notes

- Storage on the free Spaces tier is ephemeral — artifacts may be lost when the
  Space restarts. Each build is reproducible by re-submitting the same source.
- Native-only Flutter plugins (camera, BLE, etc.) cannot be tested from a web
  build. Use a real device or a paid emulator service for those.
- Source code: https://github.com/mohammadalibalwe48-hub/Flutter-app
