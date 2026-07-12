#!/bin/bash
# Apply a point-force to the hanging arm of the T-shape in Gazebo so it swings.
#
# Usage:
#   bash push-arm.sh [--seconds S] [--force N] [--location Z] [--axis Y] [--no-sample]
#
# Options:
#   -s, --seconds S     how long the force is applied, in seconds      (default 1.0)
#   -f, --force N       force magnitude in newtons; negative flips
#                       direction                                      (default 2.0)
#   -l, --location Z    point on the arm where the force acts, in the
#                       arm's own frame. 0 = at the hole (pin axis),
#                       negative = below it (e.g. -0.35 near bottom)   (default -0.35)
#   -a, --axis AXIS     direction of the force: x, y or z. The pin
#                       axis is X, so Y is the natural swing plane      (default y)
#   -n, --no-sample     apply the force but skip the settling readout
#   -h, --help          show this help and exit
#
# Examples:
#   bash push-arm.sh
#   bash push-arm.sh --force 5
#   bash push-arm.sh --seconds 0.5 --force 8 --location -0.30
#   bash push-arm.sh -f -3            # push the other way
#   bash push-arm.sh -f 4 -n          # push, no settling table

set -e

# ---- defaults ----
SECONDS_ARG=1.0
FORCE=2.0
ZLOC=-0.35
AXIS=y
SAMPLE=1

BODY="t_shape::arm"
JOINT="connector_to_arm"

usage() { sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'; }

# ---- parse named args ----
while [ $# -gt 0 ]; do
  case "$1" in
    -s|--seconds)  SECONDS_ARG="$2"; shift 2;;
    -f|--force)    FORCE="$2";       shift 2;;
    -l|--location) ZLOC="$2";        shift 2;;
    -a|--axis)     AXIS="$2";        shift 2;;
    -n|--no-sample) SAMPLE=0;        shift;;
    -h|--help)     usage; exit 0;;
    --seconds=*)   SECONDS_ARG="${1#*=}"; shift;;
    --force=*)     FORCE="${1#*=}";       shift;;
    --location=*)  ZLOC="${1#*=}";        shift;;
    --axis=*)      AXIS="${1#*=}";        shift;;
    *) echo "Unknown option: $1" >&2; echo "Try --help" >&2; exit 1;;
  esac
done

# ---- map axis -> force vector components ----
FX=0.0; FY=0.0; FZ=0.0
case "$(echo "$AXIS" | tr A-Z a-z)" in
  x) FX="$FORCE";;
  y) FY="$FORCE";;
  z) FZ="$FORCE";;
  *) echo "Invalid --axis '$AXIS' (use x, y or z)" >&2; exit 1;;
esac

# ---- split duration into secs / nsecs ----
SECS=${SECONDS_ARG%.*}
[ "$SECS" = "$SECONDS_ARG" ] && FRAC=0 || FRAC=0.${SECONDS_ARG#*.}
NSECS=$(printf "%.0f" "$(echo "$FRAC * 1000000000" | bc -l)")
[ -z "$SECS" ] && SECS=0

echo "Sourcing ROS Noetic..."
source /opt/ros/noetic/setup.bash

echo "Ensuring physics is running..."
rosservice call /gazebo/unpause_physics >/dev/null 2>&1 || true

echo "Clearing any previous wrench on the arm..."
rosservice call /gazebo/clear_body_wrenches "body_name: '$BODY'" >/dev/null 2>&1 || true

echo "Applying force:"
echo "  body       = $BODY"
echo "  force      = $FORCE N along $AXIS  (vector: $FX $FY $FZ)"
echo "  location   = z=$ZLOC m in arm frame (0=hole, negative=below)"
echo "  duration   = ${SECS}s ${NSECS}ns"

rosservice call /gazebo/apply_body_wrench "body_name: '$BODY'
reference_frame: '$BODY'
reference_point: {x: 0.0, y: 0.0, z: $ZLOC}
wrench:
  force:  {x: $FX, y: $FY, z: $FZ}
  torque: {x: 0.0, y: 0.0, z: 0.0}
start_time: {secs: 0, nsecs: 0}
duration: {secs: $SECS, nsecs: $NSECS}"

if [ "$SAMPLE" -eq 0 ]; then
  echo ""
  echo "Force applied. Watch the arm swing in Gazebo."
  exit 0
fi

echo ""
echo "Force applied. Watch the arm swing in Gazebo."
echo "Sampling joint angle & angular velocity as it settles..."
echo "  t(s)    angle(rad)    rate(rad/s)"
for i in $(seq 1 12); do
  PROPS=$(rosservice call /gazebo/get_joint_properties "joint_name: '$JOINT'" 2>/dev/null)
  ANGLE=$(echo "$PROPS" | grep '^position:' | sed 's/.*\[\(.*\)\].*/\1/')
  RATE=$( echo "$PROPS" | grep '^rate:'     | sed 's/.*\[\(.*\)\].*/\1/')
  printf "  %4.1f   %12.5f   %12.5f\n" "$(echo "$i*0.4" | bc -l)" "$ANGLE" "$RATE"
  sleep 0.4
done
echo "Done."
