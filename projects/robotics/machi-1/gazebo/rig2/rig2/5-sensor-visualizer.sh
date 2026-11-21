#!/bin/bash
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
export VIEWER_PORT="${VIEWER_PORT:-8790}"
export PHONE_PORT="${PHONE_PORT:-8791}"
exec bash "$HERE/5-sensor-visualizer.sh" "$@"