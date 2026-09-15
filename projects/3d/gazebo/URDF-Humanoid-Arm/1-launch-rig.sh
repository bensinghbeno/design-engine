#!/bin/bash
# Launch the stem + crossbar rig in Gazebo Classic.
#
# Usage:
#   bash 1-launch-rig.sh
#   bash 1-launch-rig.sh --no-gui
#   bash 1-launch-rig.sh --stem-height 2.0
#   bash 1-launch-rig.sh --crossbar-length 1.4 --crossbar-thickness 0.1
#   bash 1-launch-rig.sh --arm-side -1        # hang the arm off the other end

ARM="$(cd "$(dirname "$0")" && pwd)"

export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages
export PYTHONNOUSERSITE=1   # stale ~/.local cffi breaks rospy tooling otherwise

GUI=true
STEM_H=1.5
STEM_W=0.10
STEM_D=0.10
CB_L=1.00
CB_T=0.08
CB_D=0.08
ARM_SIDE=1
while [ $# -gt 0 ]; do
  case "$1" in
    --no-gui)             GUI=false;  shift;;
    --stem-height)        STEM_H="$2"; shift 2;;
    --stem-width)         STEM_W="$2"; shift 2;;
    --stem-depth)         STEM_D="$2"; shift 2;;
    --crossbar-length)    CB_L="$2";   shift 2;;
    --crossbar-thickness) CB_T="$2";   shift 2;;
    --crossbar-depth)     CB_D="$2";   shift 2;;
    --arm-side)           ARM_SIDE="$2"; shift 2;;
    -h|--help)     sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "Unknown option: $1" >&2; exit 1;;
  esac
done

echo "[1/3] Stopping any existing Gazebo..."
pkill -9 -f "rig.launch" 2>/dev/null
pkill -9 -f spawn_model  2>/dev/null
pkill -9 -f gzclient     2>/dev/null
pkill -9 -f gzserver     2>/dev/null
sleep 2
pkill -9 -f gzclient 2>/dev/null
pkill -9 -f gzserver 2>/dev/null
sleep 1

echo "[2/3] Sourcing ROS Noetic..."
source /opt/ros/noetic/setup.bash
export ROS_PACKAGE_PATH=$ARM:$ROS_PACKAGE_PATH

echo "[3/3] Launching Gazebo (gui=$GUI, stem ${STEM_D}x${STEM_W}x${STEM_H} m, crossbar ${CB_L} m)..."
roslaunch "$ARM/launch/rig.launch" \
  gui:=$GUI \
  stem_height:=$STEM_H \
  stem_width:=$STEM_W \
  stem_depth:=$STEM_D \
  crossbar_length:=$CB_L \
  crossbar_thickness:=$CB_T \
  crossbar_depth:=$CB_D \
  arm_side:=$ARM_SIDE
