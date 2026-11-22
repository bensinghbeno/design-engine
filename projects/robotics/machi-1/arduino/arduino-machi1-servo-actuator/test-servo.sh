#!/usr/bin/env bash
set -euo pipefail

sketch_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
port="${1:-/dev/ttyUSB0}"
fqbn="${FQBN:-arduino:avr:uno}"

command -v arduino-cli >/dev/null
command -v script >/dev/null
printf 'Board: %s | Port: %s\n' "$fqbn" "$port"
printf 'Startup commands center (135 degrees / 1500 us), without calibration. Keep the mechanism clear.\n'
arduino-cli compile --fqbn "$fqbn" --upload --port "$port" "$sketch_dir"

mkdir -p "$sketch_dir/logs"
log_path="$sketch_dir/logs/manual-servo-$(date +%Y%m%d-%H%M%S)-$$.log"
printf 'Saving terminal session to %s\n' "$log_path"
printf 'Wait for BUTTONS ARMED, then use D6/D7 or turn A0 pot. D6 overrides pot; turn knob after release to take over. Manual mode: angles after READY. Ctrl+C exits.\n'
printf -v monitor_command '%q ' arduino-cli monitor --port "$port" --config baudrate=115200
script --quiet --return --flush --command "$monitor_command" "$log_path"