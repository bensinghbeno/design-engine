#!/bin/bash
# Start the standalone Sensor Logger gripper-motion visualizer.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ ! -d "$HERE/workspace-viewer/node_modules/three" ]; then
  cd "$HERE/workspace-viewer"
  npm ci --omit=dev
fi
cd "$HERE/motion-visualizer"
exec node server.mjs "$@"