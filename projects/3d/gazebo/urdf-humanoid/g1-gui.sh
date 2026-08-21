#!/bin/bash
# Launch the interactive slider GUI for the G1 torso rig.
# One horizontal slider per arm joint; centre = gravity-rest pose.
# Requires Gazebo already running (bash launch-g1-torso.sh).

export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONNOUSERSITE=1   # stale ~/.local cffi breaks rospy otherwise
source /opt/ros/noetic/setup.bash 2>/dev/null

exec /usr/bin/python3 "$(dirname "$0")/g1_gui.py" "$@"
