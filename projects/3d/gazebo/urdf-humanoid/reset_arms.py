#!/usr/bin/env python3
"""Reset all G1 arm joints to hanging rest, deterministically.

Applying a corrective torque is unreliable: the arms are light, so even a few
Nm flips a joint past vertical, after which gravity drags it into the far
limit stop - which is exactly how the naive version made things worse.

Instead this pauses physics, writes every arm joint straight to zero via
set_model_configuration, then unpauses and lets them settle. There are no
controllers on this rig, so nothing fights the write.
"""
import sys
import rospy
from gazebo_msgs.srv import (SetModelConfiguration, GetJointProperties,
                             JointRequest, GetWorldProperties)
from std_srvs.srv import Empty

ARM_JOINTS = [
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint", "left_elbow_joint",
    "left_wrist_roll_joint", "left_wrist_pitch_joint", "left_wrist_yaw_joint",
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint", "right_elbow_joint",
    "right_wrist_roll_joint", "right_wrist_pitch_joint", "right_wrist_yaw_joint",
]


def main():
    rospy.init_node("g1_reset_arms", anonymous=True, disable_signals=True)
    rospy.wait_for_service("/gazebo/set_model_configuration", timeout=10)

    world = rospy.ServiceProxy("/gazebo/get_world_properties", GetWorldProperties)
    pause = rospy.ServiceProxy("/gazebo/pause_physics", Empty)
    unpause = rospy.ServiceProxy("/gazebo/unpause_physics", Empty)
    setcfg = rospy.ServiceProxy("/gazebo/set_model_configuration",
                                SetModelConfiguration)
    getj = rospy.ServiceProxy("/gazebo/get_joint_properties", GetJointProperties)
    clearj = rospy.ServiceProxy("/gazebo/clear_joint_forces", JointRequest)

    model = "g1_torso"
    try:
        for m in world().model_names:
            if m.startswith("g1"):
                model = m
                break
    except Exception:
        pass

    for j in ARM_JOINTS:
        try:
            clearj(j)
        except Exception:
            pass

    pause()
    resp = setcfg(model_name=model,
                  urdf_param_name="robot_description",
                  joint_names=ARM_JOINTS,
                  joint_positions=[0.0] * len(ARM_JOINTS))
    unpause()

    print(f"  model={model}  reset success={resp.success}")
    if not resp.success:
        print(f"  {resp.status_message}")
        sys.exit(1)

    rospy.sleep(4.0)
    print("  settled at rest:")
    for j in ("left_shoulder_pitch_joint", "right_shoulder_pitch_joint",
              "left_elbow_joint", "right_elbow_joint"):
        try:
            print(f"    {j:30s} {getj(j).position[0]:+.4f}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
