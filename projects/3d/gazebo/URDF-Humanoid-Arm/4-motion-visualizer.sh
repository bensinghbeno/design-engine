#!/bin/bash
# Start the standalone Sensor Logger gripper-motion visualizer.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-8766}"
export PORT
if [ ! -d "$HERE/workspace-viewer/node_modules/three" ]; then
  cd "$HERE/workspace-viewer"
  npm ci --omit=dev
fi
listeners="$(fuser -n tcp "$PORT" 2>/dev/null || true)"
for pid in $listeners; do
  process_dir="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
  process_args="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  if [[ "$process_dir" == "$HERE/motion-visualizer" && "$process_args" == *server.mjs* ]]; then
    echo "Stopping existing motion visualizer on port $PORT (PID $pid)..."
    kill "$pid"
  else
    echo "Port $PORT is in use by another process (PID $pid); leaving it untouched." >&2
    exit 1
  fi
done
cd "$HERE/motion-visualizer"
exec node server.mjs "$@"