#!/usr/bin/env bash
# Ensure the data volume is writable by the app user, then drop privileges.
set -euo pipefail

DATA_DIR="${FLUTTER_TESTER_DATA_DIR:-/data}"
mkdir -p "$DATA_DIR"
chown -R app:app "$DATA_DIR"

exec gosu app "$@"
