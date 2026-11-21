#!/bin/bash
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
exec "${PYTHON:-$HERE/.venv/bin/python}" "$HERE/screen_to_camera.py" "$@"