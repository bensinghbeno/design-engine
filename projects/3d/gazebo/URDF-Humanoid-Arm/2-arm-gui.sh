#!/bin/bash
# Slider GUI for the upper arm's shoulder angle (0-360 degrees).
#
# Launch the rig FIRST in another terminal:
#   bash 1-launch-rig.sh
#
# Then:
#   bash 2-arm-gui.sh

ARM="$(cd "$(dirname "$0")" && pwd)"

export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages
export PYTHONNOUSERSITE=1   # stale ~/.local cffi breaks rospy tooling otherwise

source /opt/ros/noetic/setup.bash
export ROS_PACKAGE_PATH=$ARM:$ROS_PACKAGE_PATH

exec /usr/bin/python3 "$ARM/arm_gui.py" "$@"
