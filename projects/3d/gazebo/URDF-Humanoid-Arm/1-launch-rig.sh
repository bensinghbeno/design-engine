#!/bin/bash
# Launch the rig in Gazebo Classic, with the shoulder slider GUI alongside.
#
# The slider GUI starts automatically once Gazebo is actually up - it waits
# for /gazebo/set_model_configuration rather than racing it - and is killed
# again when this script exits.
#
# Usage:
#   bash 1-launch-rig.sh
#   bash 1-launch-rig.sh --no-gui             # headless, no Gazebo window
#   bash 1-launch-rig.sh --no-slider          # Gazebo only, no slider GUI
#   bash 1-launch-rig.sh --stem-height 2.0
#   bash 1-launch-rig.sh --crossbar-length 1.4 --crossbar-thickness 0.1
#   bash 1-launch-rig.sh --arm-side -1        # hang the arm off the other end
#   bash 1-launch-rig.sh --density 680        # birch ply instead of softwood

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
DENSITY=500
SLIDER=true
while [ $# -gt 0 ]; do
  case "$1" in
    --no-gui)             GUI=false;  shift;;
    --no-slider)          SLIDER=false; shift;;
    --stem-height)        STEM_H="$2"; shift 2;;
    --stem-width)         STEM_W="$2"; shift 2;;
    --stem-depth)         STEM_D="$2"; shift 2;;
    --crossbar-length)    CB_L="$2";   shift 2;;
    --crossbar-thickness) CB_T="$2";   shift 2;;
    --crossbar-depth)     CB_D="$2";   shift 2;;
    --arm-side)           ARM_SIDE="$2"; shift 2;;
    --density)            DENSITY="$2"; shift 2;;
    -h|--help)     sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "Unknown option: $1" >&2; exit 1;;
  esac
done

echo "[1/4] Stopping any existing Gazebo..."
pkill -9 -f "rig.launch" 2>/dev/null
pkill -9 -f arm_gui.py   2>/dev/null
pkill -9 -f spawn_model  2>/dev/null
pkill -9 -f gzclient     2>/dev/null
pkill -9 -f gzserver     2>/dev/null
sleep 2
pkill -9 -f gzclient 2>/dev/null
pkill -9 -f gzserver 2>/dev/null
sleep 1

echo "[2/4] Sourcing ROS Noetic..."
source /opt/ros/noetic/setup.bash
export ROS_PACKAGE_PATH=$ARM:$ROS_PACKAGE_PATH

# Tear the slider GUI down with the sim, however this script exits.
GUI_PID=""
cleanup() {
  [ -n "$GUI_PID" ] && kill "$GUI_PID" 2>/dev/null
  pkill -f arm_gui.py 2>/dev/null
}
trap cleanup EXIT INT TERM

if [ "$SLIDER" = true ]; then
  echo "[3/4] Slider GUI will start once Gazebo is up..."
  (
    # Wait for the service the GUI needs, rather than racing Gazebo and
    # aborting. Give up after ~60 s so this never hangs around forever.
    for _ in $(seq 60); do
      if rosservice list 2>/dev/null | grep -q /gazebo/set_model_configuration
      then
        sleep 1            # let the model finish spawning
        exec /usr/bin/python3 "$ARM/arm_gui.py"
      fi
      sleep 1
    done
    echo "[slider] Gazebo never came up - GUI not started." >&2
  ) &
  GUI_PID=$!
else
  echo "[3/4] Slider GUI disabled (--no-slider)."
fi

echo "[4/4] Launching Gazebo (gui=$GUI, stem ${STEM_D}x${STEM_W}x${STEM_H} m, crossbar ${CB_L} m)..."
roslaunch "$ARM/launch/rig.launch" \
  gui:=$GUI \
  stem_height:=$STEM_H \
  stem_width:=$STEM_W \
  stem_depth:=$STEM_D \
  crossbar_length:=$CB_L \
  crossbar_thickness:=$CB_T \
  crossbar_depth:=$CB_D \
  arm_side:=$ARM_SIDE \
  density:=$DENSITY
