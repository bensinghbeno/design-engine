#!/bin/bash
# Launch the Unitree G1 UPPER BODY on a static pole.
# Run start-ros-claude-bridge.sh FIRST in another terminal.
#
# No legs, no controllers, no PID - the arms are fully passive and hang under
# gravity. This is the clean setup for force / joint experiments.
#
# Usage:
#   bash launch-g1-torso.sh
#   bash launch-g1-torso.sh --no-gui
#   bash launch-g1-torso.sh --pole-height 1.2
#
# Then poke it with:  bash g1-arm.sh push -l left_elbow_link -f 40

HUM=/home/ben/dev/design-engine/projects/3d/gazebo/urdf-humanoid

export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages
export PYTHONNOUSERSITE=1   # stale ~/.local cffi breaks rosservice otherwise

GUI=true
POLE_H=1.0
POLE_R=0.05
while [ $# -gt 0 ]; do
  case "$1" in
    --no-gui)      GUI=false;  shift;;
    --pole-height) POLE_H="$2"; shift 2;;
    --pole-radius) POLE_R="$2"; shift 2;;
    -h|--help)     sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "Unknown option: $1" >&2; exit 1;;
  esac
done

echo "[1/4] Stopping any existing Gazebo..."
pkill -9 -f "g1.launch"       2>/dev/null
pkill -9 -f "g1_stand.launch" 2>/dev/null
pkill -9 -f "g1_torso.launch" 2>/dev/null
pkill -9 -f spawn_model       2>/dev/null
pkill -9 -f gzclient          2>/dev/null
pkill -9 -f gzserver          2>/dev/null
sleep 2
pkill -9 -f gzclient 2>/dev/null
pkill -9 -f gzserver 2>/dev/null
sleep 2

echo "[2/4] Sourcing ROS Noetic..."
source /opt/ros/noetic/setup.bash
export ROS_PACKAGE_PATH=$HUM:$ROS_PACKAGE_PATH

echo "[3/4] Generating torso URDF (legs removed, pole added)..."
/usr/bin/python3 "$HUM/make_g1.py" --torso \
  --pole-height "$POLE_H" --pole-radius "$POLE_R" \
  || { echo "make_g1.py failed"; exit 1; }

echo "[4/4] Launching Gazebo (gui=$GUI)..."
roslaunch "$HUM/launch/g1_torso.launch" gui:=$GUI
