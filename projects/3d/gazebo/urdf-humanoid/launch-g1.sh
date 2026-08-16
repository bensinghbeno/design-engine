#!/bin/bash
# (2) Launch Gazebo with the Unitree G1 humanoid.
#     Run start-ros-claude-bridge.sh FIRST in another terminal.
#
# Usage:
#   bash launch-g1.sh              # pelvis pinned to world (recommended)
#   bash launch-g1.sh --free       # free-floating, will topple
#   bash launch-g1.sh --no-gui     # headless

HUM=/home/ben/dev/design-engine/projects/3d/gazebo/urdf-humanoid

export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages
# Ignore ~/.local site-packages: a stale cffi 1.17.1 there shadows system cffi
# 1.14.0 and breaks rosbag/rostopic/rosservice with a version mismatch.
export PYTHONNOUSERSITE=1

PINNED=true
GUI=true
while [ $# -gt 0 ]; do
  case "$1" in
    --free)    PINNED=false; shift;;
    --pinned)  PINNED=true;  shift;;
    --no-gui)  GUI=false;    shift;;
    -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "Unknown option: $1" >&2; exit 1;;
  esac
done

echo "[1/4] Stopping any existing Gazebo..."
pkill -9 -f "g1.launch"  2>/dev/null
pkill -9 -f spawn_model  2>/dev/null
pkill -9 -f gzclient     2>/dev/null
pkill -9 -f gzserver     2>/dev/null
sleep 2
pkill -9 -f gzclient 2>/dev/null
pkill -9 -f gzserver 2>/dev/null
sleep 2

echo "[2/4] Sourcing ROS Noetic..."
source /opt/ros/noetic/setup.bash
export ROS_PACKAGE_PATH=$HUM:$ROS_PACKAGE_PATH

echo "[3/4] Regenerating G1 URDFs (fixes relative mesh paths)..."
/usr/bin/python3 "$HUM/make_g1.py" >/dev/null || { echo "make_g1.py failed"; exit 1; }

echo "[4/4] Launching Gazebo (pinned=$PINNED gui=$GUI)..."
roslaunch "$HUM/launch/g1.launch" pinned:=$PINNED gui:=$GUI
