#!/bin/bash
# Seven G1-order arm sliders, each -180..+180 degrees with zero centred,
# plus one 0..80 mm aperture slider commanding both physical gripper fingers.
# Uses system Python (Tk + ROS); the editor's Python may not include Tk.
#
# The rig launcher normally opens this GUI automatically. For a separate GUI,
# launch the rig FIRST in another terminal without its automatic sliders:
#   bash 1-launch-rig.sh --no-slider
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
