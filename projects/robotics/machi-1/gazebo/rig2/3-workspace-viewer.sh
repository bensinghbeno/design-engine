#!/bin/bash
# Start the local reachable-workspace viewer; no Gazebo session required.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/workspace-viewer"
if [ ! -d node_modules/three ]; then
  echo "Installing local viewer dependencies (first run requires internet)..."
  npm ci --omit=dev
fi
exec node server.mjs "$@"