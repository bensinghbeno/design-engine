#!/usr/bin/env bash
set -euo pipefail
directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
device="${1:-/dev/ttyUSB0}"
authority="${XAUTHORITY:-$HOME/.Xauthority}"
app="$directory/tools/squashfs-root"
image="robstride00-motorstudio:ubuntu22.04"
[[ -n "${DISPLAY:-}" && -r "$authority" ]] || { printf 'X11 DISPLAY and readable Xauthority required.\n' >&2; exit 1; }
[[ -c "$device" ]] || { printf 'Missing serial device: %s\n' "$device" >&2; exit 1; }
[[ -x "$app/AppRun" ]] || { printf 'Extract motor_tool.AppImage in robstride00/tools first.\n' >&2; exit 1; }
docker info >/dev/null
if ! docker image inspect "$image" >/dev/null 2>&1; then
    docker build -t "$image" - < "$directory/Dockerfile.motorstudio"
fi
printf 'Opening MotorStudio; no automatic motor connection or motion is requested.\n'
exec docker run --rm --name robstride00-motorstudio \
    --user "$(id -u):$(id -g)" --group-add "$(stat -c %g "$device")" \
    --hostname "$(hostname)" --network none --cap-drop ALL \
    --security-opt no-new-privileges --device "$device:$device" \
    -e "DISPLAY=$DISPLAY" -e XAUTHORITY=/tmp/motorstudio.xauth \
    --mount "type=bind,src=$authority,dst=/tmp/motorstudio.xauth,readonly" \
    --mount type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix,readonly \
    --mount "type=bind,src=$app,dst=/opt/motorstudio,readonly" \
    "$image"