#!/bin/bash
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
export PORT="${PORT:-8785}"
exec bash "$HERE/3-workspace-viewer.sh" "$@"