#!/bin/bash
# Poke the Unitree G1's arms in Gazebo: apply forces, apply joint torques,
# or snap joints to an angle. Mirrors the style of push-arm.sh.
#
# Usage:
#   bash g1-arm.sh push   [-l LINK]  [-f N] [-a x|y|z] [-s SEC]
#   bash g1-arm.sh torque [-j JOINT] [-t NM]           [-s SEC]
#   bash g1-arm.sh pose   [-j JOINT] [-p RAD]
#   bash g1-arm.sh wave
#   bash g1-arm.sh read
#   bash g1-arm.sh joints
#
# Modes:
#   push    apply a point force to an arm LINK (it swings, then sags back)
#   torque  apply a torque about a JOINT axis  (rotates that joint)
#   pose    instantly set a JOINT to an angle (pauses physics, sets, resumes)
#   wave    scripted demo: raises then lowers the left arm
#   read    print current angle of every arm joint
#   joints  list all G1 joint names
#
# Options:
#   -l, --link   LINK    default left_elbow_link
#   -j, --joint  JOINT   default left_shoulder_pitch_joint
#   -f, --force  N       force in newtons        (default 30)
#   -t, --torque NM      torque in newton-metres (default 15)
#   -p, --position RAD   target angle in radians (default -1.0)
#   -a, --axis   x|y|z   force direction         (default y)
#   -s, --seconds SEC    how long to apply       (default 0.5)
#   -h, --help

export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONNOUSERSITE=1   # stale ~/.local cffi breaks rosservice otherwise
source /opt/ros/noetic/setup.bash 2>/dev/null

MODEL=g1
LINK=left_elbow_link
JOINT=left_shoulder_pitch_joint
FORCE=30
TORQUE=15
POSITION=-1.0
AXIS=y
SECS=0.5

MODE=$1; shift 2>/dev/null
[ -z "$MODE" ] && { sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit 0; }

while [ $# -gt 0 ]; do
  case "$1" in
    -l|--link)     LINK="$2";     shift 2;;
    -j|--joint)    JOINT="$2";    shift 2;;
    -f|--force)    FORCE="$2";    shift 2;;
    -t|--torque)   TORQUE="$2";   shift 2;;
    -p|--position) POSITION="$2"; shift 2;;
    -a|--axis)     AXIS="$2";     shift 2;;
    -s|--seconds)  SECS="$2";     shift 2;;
    -h|--help)     sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "Unknown option: $1" >&2; exit 1;;
  esac
done

# split float seconds into secs/nsecs
S=${SECS%.*}; [ -z "$S" ] && S=0
[ "$S" = "$SECS" ] && FRAC=0 || FRAC=0.${SECS#*.}
NS=$(printf "%.0f" "$(echo "$FRAC * 1000000000" | bc -l)")

ARM_JOINTS="left_shoulder_pitch_joint left_shoulder_roll_joint left_shoulder_yaw_joint
left_elbow_joint left_wrist_roll_joint left_wrist_pitch_joint left_wrist_yaw_joint
right_shoulder_pitch_joint right_shoulder_roll_joint right_shoulder_yaw_joint
right_elbow_joint right_wrist_roll_joint right_wrist_pitch_joint right_wrist_yaw_joint"

read_joint() {
  rosservice call /gazebo/get_joint_properties "joint_name: '$1'" 2>/dev/null \
    | grep '^position:' | sed 's/.*\[\(.*\)\].*/\1/'
}

case "$MODE" in

  joints)
    rosservice call /gazebo/get_world_properties >/dev/null 2>&1 || { echo "Gazebo not running."; exit 1; }
    echo "G1 arm joints:"; for j in $ARM_JOINTS; do echo "  $j"; done
    ;;

  read)
    echo "  joint                             angle(rad)"
    for j in $ARM_JOINTS; do printf "  %-32s %s\n" "$j" "$(read_joint "$j")"; done
    ;;

  push)
    rosservice call /gazebo/unpause_physics >/dev/null 2>&1
    FX=0; FY=0; FZ=0
    case "$(echo "$AXIS" | tr A-Z a-z)" in
      x) FX=$FORCE;; y) FY=$FORCE;; z) FZ=$FORCE;;
      *) echo "bad --axis"; exit 1;;
    esac
    echo "Pushing $MODEL::$LINK with ${FORCE}N along $AXIS for ${SECS}s"
    rosservice call /gazebo/clear_body_wrenches "body_name: '$MODEL::$LINK'" >/dev/null 2>&1
    rosservice call /gazebo/apply_body_wrench "body_name: '$MODEL::$LINK'
reference_frame: ''
reference_point: {x: 0.0, y: 0.0, z: 0.0}
wrench:
  force:  {x: $FX, y: $FY, z: $FZ}
  torque: {x: 0.0, y: 0.0, z: 0.0}
start_time: {secs: 0, nsecs: 0}
duration: {secs: $S, nsecs: $NS}"
    echo; echo "  t(s)   $JOINT"
    for i in $(seq 1 10); do
      printf "  %4.1f   %s\n" "$(echo "$i*0.4" | bc -l)" "$(read_joint "$JOINT")"
      sleep 0.4
    done
    ;;

  torque)
    rosservice call /gazebo/unpause_physics >/dev/null 2>&1
    echo "Applying ${TORQUE}Nm to $JOINT for ${SECS}s"
    rosservice call /gazebo/clear_joint_forces "joint_name: '$JOINT'" >/dev/null 2>&1
    rosservice call /gazebo/apply_joint_effort "joint_name: '$JOINT'
effort: $TORQUE
start_time: {secs: 0, nsecs: 0}
duration: {secs: $S, nsecs: $NS}"
    echo; echo "  t(s)   angle(rad)"
    for i in $(seq 1 10); do
      printf "  %4.1f   %s\n" "$(echo "$i*0.4" | bc -l)" "$(read_joint "$JOINT")"
      sleep 0.4
    done
    ;;

  pose)
    echo "Setting $JOINT -> $POSITION rad"
    rosservice call /gazebo/pause_physics >/dev/null 2>&1
    rosservice call /gazebo/set_model_configuration "model_name: '$MODEL'
urdf_param_name: 'robot_description'
joint_names: ['$JOINT']
joint_positions: [$POSITION]"
    rosservice call /gazebo/unpause_physics >/dev/null 2>&1
    sleep 0.5
    echo "  now at: $(read_joint "$JOINT")"
    echo "  NOTE: with no controller the joint will sag back under gravity."
    ;;

  wave)
    echo "Waving left arm (pose steps, physics paused each step)..."
    for a in -1.4 -0.9 -1.4 -0.9 -1.4; do
      rosservice call /gazebo/pause_physics >/dev/null 2>&1
      rosservice call /gazebo/set_model_configuration "model_name: '$MODEL'
urdf_param_name: 'robot_description'
joint_names: ['left_shoulder_pitch_joint','left_shoulder_roll_joint','left_elbow_joint']
joint_positions: [$a, 0.3, 1.0]" >/dev/null
      rosservice call /gazebo/unpause_physics >/dev/null 2>&1
      sleep 0.6
    done
    echo "Done."
    ;;

  *) echo "Unknown mode '$MODE'. Try --help"; exit 1;;
esac
