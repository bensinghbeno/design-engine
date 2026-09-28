#!/bin/bash
# Start the gripper-motion visualizer: CSV replay plus live Pixel sensor streaming.
# Viewer: http://127.0.0.1:$PORT (this computer only).
# Phone:  https://$LAN_IP:$STREAM_PORT (worker-thread server; self-signed cert, same Wi-Fi).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-8766}"
STREAM_PORT="${STREAM_PORT:-8767}"
LAN_IP="${LAN_IP:-$(hostname -I | awk '{print $1}')}"
export PORT STREAM_PORT LAN_IP
if [ ! -d "$HERE/workspace-viewer/node_modules/three" ]; then
  cd "$HERE/workspace-viewer"
  npm ci --omit=dev
fi

# Chrome only exposes motion sensors on HTTPS pages, so the phone server needs a certificate for this IP.
CERT_DIR="$HERE/motion-visualizer/.certs"
if [[ ! -f "$CERT_DIR/cert.pem" || "$(cat "$CERT_DIR/ip" 2>/dev/null)" != "$LAN_IP" ]]; then
  echo "Creating self-signed certificate for $LAN_IP..."
  mkdir -p "$CERT_DIR"
  openssl req -x509 -newkey rsa:2048 -nodes -days 825 -subj "/CN=Motion Lab $LAN_IP" \
    -addext "subjectAltName=IP:$LAN_IP,IP:127.0.0.1,DNS:localhost" \
    -keyout "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" 2>/dev/null
  chmod 600 "$CERT_DIR/key.pem"
  echo "$LAN_IP" > "$CERT_DIR/ip"
fi

stopped=""
for port in "$PORT" "$STREAM_PORT"; do
  for pid in $(fuser -n tcp "$port" 2>/dev/null || true); do
    [[ " $stopped " == *" $pid "* ]] && continue
    process_dir="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
    process_args="$(ps -p "$pid" -o args= 2>/dev/null || true)"
    if [[ "$process_dir" == "$HERE/motion-visualizer" && "$process_args" == *server.mjs* ]]; then
      echo "Stopping existing motion visualizer on port $port (PID $pid)..."
      kill "$pid" 2>/dev/null || true
      stopped="$stopped $pid"
    else
      echo "Port $port is in use by another process (PID $pid); leaving it untouched." >&2
      exit 1
    fi
  done
done
for _ in $(seq 50); do
  [[ -z "$(fuser -n tcp "$PORT" 2>/dev/null)$(fuser -n tcp "$STREAM_PORT" 2>/dev/null)" ]] && break
  sleep 0.1
done
cd "$HERE/motion-visualizer"
exec node server.mjs "$@"