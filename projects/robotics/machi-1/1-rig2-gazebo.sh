#!/bin/bash
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
exec bash "$HERE/gazebo/rig2/7-launch-rig2.sh" "$@"