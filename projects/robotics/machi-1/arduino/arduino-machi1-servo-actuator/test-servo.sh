#!/usr/bin/env bash
set -euo pipefail

sketch_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
port="${1:-/dev/ttyUSB0}"
fqbn="${FQBN:-arduino:avr:uno}"

command -v arduino-cli >/dev/null
command -v script >/dev/null
printf 'Board: %s | Port: %s\n' "$fqbn" "$port"
printf 'Startup may calibrate near center. Keep the mechanism clear.\n'
arduino-cli compile --fqbn "$fqbn" --upload --port "$port" "$sketch_dir"

mkdir -p "$sketch_dir/logs"
log_path="$sketch_dir/logs/manual-servo-$(date +%Y%m%d-%H%M%S)-$$.log"
printf 'Saving terminal session to %s\n' "$log_path"
printf 'Automatic mode: wait for BUTTONS ARMED, then use D6/D7. Manual mode: enter angles after READY. Ctrl+C exits.\n'
printf -v monitor_command '%q ' arduino-cli monitor --port "$port" --config baudrate=115200
script --quiet --return --flush --command "$monitor_command" "$log_path"