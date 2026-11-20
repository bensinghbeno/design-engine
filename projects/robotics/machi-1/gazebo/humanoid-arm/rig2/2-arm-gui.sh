#!/bin/bash
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages
export PYTHONNOUSERSITE=1
source /opt/ros/noetic/setup.bash
export ROS_PACKAGE_PATH="$HERE:${ROS_PACKAGE_PATH:-}"
exec /usr/bin/python3 "$HERE/rig2/arm_gui.py" "$@"