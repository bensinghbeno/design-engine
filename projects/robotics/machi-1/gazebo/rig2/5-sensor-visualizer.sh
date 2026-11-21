#!/bin/bash
# Start the standalone live phone-sensor dashboard (app 5).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
VIEWER_PORT="${VIEWER_PORT:-8770}"
PHONE_PORT="${PHONE_PORT:-8771}"
LAN_IP="${LAN_IP:-$(hostname -I | awk '{print $1}')}"
export VIEWER_PORT PHONE_PORT LAN_IP
CERT_DIR="$HERE/sensor-visualizer/.certs"
if [[ ! -f "$CERT_DIR/cert.pem" || "$(cat "$CERT_DIR/ip" 2>/dev/null)" != "$LAN_IP" ]]; then
  mkdir -p "$CERT_DIR"
  openssl req -x509 -newkey rsa:2048 -nodes -days 825 -subj "/CN=Sensor Lab $LAN_IP" \
    -addext "subjectAltName=IP:$LAN_IP,IP:127.0.0.1,DNS:localhost" \
    -keyout "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" 2>/dev/null
  chmod 600 "$CERT_DIR/key.pem"
  echo "$LAN_IP" > "$CERT_DIR/ip"
fi

stopped=""
for port in "$VIEWER_PORT" "$PHONE_PORT"; do
  for pid in $(fuser -n tcp "$port" 2>/dev/null || true); do
    [[ " $stopped " == *" $pid "* ]] && continue
    process_dir="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
    process_args="$(ps -p "$pid" -o args= 2>/dev/null || true)"
    if [[ "$process_dir" == "$HERE/sensor-visualizer" && "$process_args" == *server.mjs* ]]; then
      echo "Stopping existing sensor visualizer on port $port (PID $pid)..."
      kill "$pid" 2>/dev/null || true
      stopped="$stopped $pid"
    else
      echo "Port $port is in use by another process (PID $pid); leaving it untouched." >&2
      exit 1
    fi
  done
done
for _ in $(seq 50); do
  [[ -z "$(fuser -n tcp "$VIEWER_PORT" 2>/dev/null)$(fuser -n tcp "$PHONE_PORT" 2>/dev/null)" ]] && break
  sleep 0.1
done
cd "$HERE/sensor-visualizer"
exec node server.mjs
