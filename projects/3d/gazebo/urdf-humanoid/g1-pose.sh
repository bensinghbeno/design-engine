#!/bin/bash
# Command the Unitree G1 into a pose using the position controllers.
# Requires launch-g1-stand.sh to be running.
#
# Usage:
#   bash g1-pose.sh stand      # upright neutral stance
#   bash g1-pose.sh ready      # slight knee bend, arms forward
#   bash g1-pose.sh tpose      # arms straight out sideways
#   bash g1-pose.sh armsup     # both arms raised overhead
#   bash g1-pose.sh wave       # animated wave with the right arm
#   bash g1-pose.sh read       # print current joint angles
#   bash g1-pose.sh set JOINT RAD    # drive one joint
#
# Every joint is held by a PID position controller, so poses are maintained
# against gravity instead of sagging.

export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONNOUSERSITE=1
source /opt/ros/noetic/setup.bash 2>/dev/null

NS=/g1
pub() {  # pub <joint> <value>
  rostopic pub -1 "$NS/$1_position_controller/command" std_msgs/Float64 "data: $2" >/dev/null 2>&1
}

ALL_JOINTS="left_hip_pitch_joint left_hip_roll_joint left_hip_yaw_joint
left_knee_joint left_ankle_pitch_joint left_ankle_roll_joint
right_hip_pitch_joint right_hip_roll_joint right_hip_yaw_joint
right_knee_joint right_ankle_pitch_joint right_ankle_roll_joint
left_shoulder_pitch_joint left_shoulder_roll_joint left_shoulder_yaw_joint
left_elbow_joint left_wrist_roll_joint left_wrist_pitch_joint left_wrist_yaw_joint
right_shoulder_pitch_joint right_shoulder_roll_joint right_shoulder_yaw_joint
right_elbow_joint right_wrist_roll_joint right_wrist_pitch_joint right_wrist_yaw_joint"

# Waist joints are welded rigid by default (see launch-g1-stand.sh). If you
# launched with --live-waist, add them back so poses drive them too.
if rostopic list 2>/dev/null | grep -q "waist_yaw_joint_position_controller"; then
  ALL_JOINTS="$ALL_JOINTS waist_yaw_joint waist_roll_joint waist_pitch_joint"
fi

zero_all() { for j in $ALL_JOINTS; do pub "$j" 0.0; done; }

MODE=${1:-stand}

case "$MODE" in

  stand)
    echo "Pose: STAND (straight upright, arms at sides)"
    zero_all
    # arms hang naturally rather than sticking out
    pub left_shoulder_roll_joint   0.15
    pub right_shoulder_roll_joint -0.15
    pub left_elbow_joint           0.1
    pub right_elbow_joint          0.1
    ;;

  ready)
    echo "Pose: READY (athletic stance, knees bent, arms forward)"
    zero_all
    for s in left right; do
      pub ${s}_hip_pitch_joint    -0.3
      pub ${s}_knee_joint          0.6
      pub ${s}_ankle_pitch_joint  -0.3
      pub ${s}_shoulder_pitch_joint -0.4
      pub ${s}_elbow_joint         0.9
    done
    pub left_shoulder_roll_joint   0.2
    pub right_shoulder_roll_joint -0.2
    ;;

  tpose)
    echo "Pose: T-POSE (arms straight out to the sides)"
    zero_all
    pub left_shoulder_roll_joint   1.5
    pub right_shoulder_roll_joint -1.5
    ;;

  armsup)
    echo "Pose: ARMS UP (both arms overhead)"
    zero_all
    pub left_shoulder_pitch_joint  -2.6
    pub right_shoulder_pitch_joint -2.6
    pub left_shoulder_roll_joint    0.2
    pub right_shoulder_roll_joint  -0.2
    ;;

  wave)
    echo "Pose: WAVE (right arm)"
    bash "$0" stand >/dev/null
    sleep 1.5
    pub right_shoulder_pitch_joint -2.2
    pub right_shoulder_roll_joint  -0.5
    pub right_elbow_joint           1.0
    sleep 1.0
    for i in 1 2 3; do
      pub right_wrist_roll_joint  0.8; sleep 0.45
      pub right_wrist_roll_joint -0.8; sleep 0.45
    done
    pub right_wrist_roll_joint 0.0
    echo "  done"
    ;;

  set)
    [ $# -lt 3 ] && { echo "usage: $0 set JOINT RADIANS"; exit 1; }
    echo "Setting $2 -> $3 rad"
    pub "$2" "$3"
    ;;

  read)
    echo "  joint                             angle(rad)"
    for j in $ALL_JOINTS; do
      P=$(rosservice call /gazebo/get_joint_properties "joint_name: '$j'" 2>/dev/null \
          | grep '^position:' | sed 's/.*\[\(.*\)\].*/\1/')
      printf "  %-32s %s\n" "$j" "$P"
    done
    ;;

  *) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//';;
esac
