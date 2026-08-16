#!/bin/bash
# Launch the Unitree G1 STANDING UPRIGHT, held by position controllers.
# Run start-ros-claude-bridge.sh FIRST in another terminal.
#
# Usage:
#   bash launch-g1-stand.sh                # waist welded rigid (stable)
#   bash launch-g1-stand.sh --live-waist   # waist actuated (may oscillate)
#   bash launch-g1-stand.sh --no-gui
#
# The waist is locked by default: a single yaw axis carries 16.6 kg of torso
# plus arms, and under PID it limit-cycles and yaws the torso left/right
# forever. Locking removes the failure mode. Use --live-waist if you actually
# need to rotate the torso.
#
# Once it's up, drive it with:  bash g1-pose.sh stand|ready|tpose|wave

HUM=/home/ben/dev/design-engine/projects/3d/gazebo/urdf-humanoid

export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages
export PYTHONNOUSERSITE=1   # stale ~/.local cffi breaks rosservice otherwise

GUI=true
LOCK=true
while [ $# -gt 0 ]; do
  case "$1" in
    --no-gui)     GUI=false;  shift;;
    --live-waist) LOCK=false; shift;;
    --lock-waist) LOCK=true;  shift;;
    -h|--help)    sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "Unknown option: $1" >&2; exit 1;;
  esac
done

echo "[1/4] Stopping any existing Gazebo..."
pkill -9 -f "g1.launch"       2>/dev/null
pkill -9 -f "g1_stand.launch" 2>/dev/null
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

echo "[3/4] Generating controlled URDF (feet on ground, transmissions)..."
LOCKARG=""
[ "$LOCK" = "true" ] && LOCKARG="--lock-waist"
/usr/bin/python3 "$HUM/make_g1.py" --stand $LOCKARG || { echo "make_g1.py failed"; exit 1; }

echo "[4/4] Launching Gazebo + position controllers (gui=$GUI lock_waist=$LOCK)..."
roslaunch "$HUM/launch/g1_stand.launch" gui:=$GUI lock_waist:=$LOCK
