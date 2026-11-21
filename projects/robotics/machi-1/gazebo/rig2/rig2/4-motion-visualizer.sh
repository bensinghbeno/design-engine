#!/bin/bash
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
export PORT="${PORT:-8786}"
export STREAM_PORT="${STREAM_PORT:-8787}"
exec bash "$HERE/4-motion-visualizer.sh" "$@"