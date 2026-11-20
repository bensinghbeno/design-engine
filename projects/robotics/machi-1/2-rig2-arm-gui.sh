#!/bin/bash
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
exec bash "$HERE/gazebo/humanoid-arm/rig2/2-arm-gui.sh" "$@"