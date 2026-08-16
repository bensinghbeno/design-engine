#!/bin/bash
# Verify the torso-on-pole rig: arms should FALL under gravity and settle.
export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONNOUSERSITE=1
HUM=/home/ben/dev/design-engine/projects/3d/gazebo/urdf-humanoid
source /opt/ros/noetic/setup.bash
export ROS_PACKAGE_PATH=$HUM:$ROS_PACKAGE_PATH

pkill -9 -f gzserver 2>/dev/null; pkill -9 -f roslaunch 2>/dev/null; sleep 3
/usr/bin/python3 "$HUM/make_g1.py" --torso >/dev/null

echo "### launching headless..."
roslaunch "$HUM/launch/g1_torso.launch" gui:=false > /tmp/g1_torso.log 2>&1 &
sleep 16

jp() { timeout 6 rosservice call /gazebo/get_joint_properties "joint_name: '$1'" 2>/dev/null | grep '^position:' | sed 's/.*\[\(.*\)\].*/\1/'; }
lz() { timeout 6 rosservice call /gazebo/get_link_state "link_name: '$1'
reference_frame: ''" 2>/dev/null | grep -m1 'z:' | awk '{print $2}'; }

echo
echo "### model spawned?"
timeout 8 rosservice call /gazebo/get_world_properties 2>/dev/null | grep -A3 model_names | sed 's/^/  /'

echo
echo "### arms settling under gravity (shoulder_pitch, should stop changing):"
for i in 1 2 3 4 5; do
  printf "  t=%ds  L=%-22s R=%s\n" "$((i*2))" "$(jp left_shoulder_pitch_joint)" "$(jp right_shoulder_pitch_joint)"
  sleep 2
done

echo
echo "### final geometry:"
printf "  pelvis z      = %s  (pole top, expect ~1.0)\n" "$(lz pelvis)"
printf "  left elbow z  = %s  (should hang BELOW pelvis)\n" "$(lz left_elbow_link)"
printf "  left wrist z  = %s\n" "$(lz left_wrist_yaw_link)"

echo
echo "### push test: 40N on left elbow, does it swing and settle back?"
BEFORE=$(jp left_shoulder_roll_joint)
rosservice call /gazebo/apply_body_wrench "body_name: 'g1_torso::left_elbow_link'
reference_frame: ''
reference_point: {x: 0.0, y: 0.0, z: 0.0}
wrench:
  force:  {x: 0.0, y: 40.0, z: 0.0}
  torque: {x: 0.0, y: 0.0, z: 0.0}
start_time: {secs: 0, nsecs: 0}
duration: {secs: 1, nsecs: 0}" >/dev/null 2>&1
sleep 1; DURING=$(jp left_shoulder_roll_joint)
sleep 6; AFTER=$(jp left_shoulder_roll_joint)
printf "  before=%s\n  during=%s\n  settled=%s\n" "$BEFORE" "$DURING" "$AFTER"

echo
echo "### errors:"
grep -iE "error" /tmp/g1_torso.log | grep -v XmlRpc | head -4 | sed 's/^/  /'

pkill -9 -f roslaunch 2>/dev/null; pkill -9 -f gzserver 2>/dev/null
echo DONE
