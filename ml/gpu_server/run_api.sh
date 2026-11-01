#!/usr/bin/env bash
set -euo pipefail
exec uvicorn app:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8080}" --workers 1
