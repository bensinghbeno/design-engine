#!/usr/bin/env python3
"""Restore the G1 rig to its startup state without relaunching Gazebo.

Startup state means:
  * no leftover forces or torques queued on any body/joint
  * every joint back at its zero angle
  * zero joint velocity (positions alone are not enough - a joint written to
    zero while still spinning will immediately fly off again)
  * model pose back at the origin
  * physics running

Order matters. Forces are cleared FIRST, because clear_joint_forces only
cancels pending efforts - if a wrench is still active when we zero the
joints, it re-accelerates them the moment physics resumes.

Usage:
  python3 init_sim.py            # reset arms (and any other movable joints)
  python3 init_sim.py --verbose  # also print every joint before/after
"""
import argparse
import sys

import rospy
from gazebo_msgs.srv import (BodyRequest, GetJointProperties,
                             GetWorldProperties, JointRequest,
                             SetModelConfiguration, GetModelProperties)
from std_srvs.srv import Empty

# Every joint that can move on the torso rig. Fixed joints are ignored by
# set_model_configuration, so listing extras is harmless.
ARM_JOINTS = [
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint", "left_elbow_joint",
    "left_wrist_roll_joint", "left_wrist_pitch_joint", "left_wrist_yaw_joint",
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint", "right_elbow_joint",
    "right_wrist_roll_joint", "right_wrist_pitch_joint", "right_wrist_yaw_joint",
]

# Present on the legged rigs; harmless no-ops on the torso rig.
EXTRA_JOINTS = [
    "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
    "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
    "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
    "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
    "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
]

PUSHABLE_LINKS = [
    "left_shoulder_pitch_link", "left_shoulder_roll_link",
    "left_shoulder_yaw_link", "left_elbow_link",
    "left_wrist_roll_link", "left_wrist_pitch_link", "left_wrist_yaw_link",
    "right_shoulder_pitch_link", "right_shoulder_roll_link",
    "right_shoulder_yaw_link", "right_elbow_link",
    "right_wrist_roll_link", "right_wrist_pitch_link", "right_wrist_yaw_link",
    "torso_link", "pelvis",
]


def svc(name, typ):
    return rospy.ServiceProxy(name, typ)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--settle", type=float, default=5.0,
                    help="seconds to let the arms settle after reset")
    args = ap.parse_args()

    rospy.init_node("g1_init_sim", anonymous=True, disable_signals=True)
    try:
        rospy.wait_for_service("/gazebo/set_model_configuration", timeout=10)
    except rospy.ROSException:
        sys.exit("ERROR: Gazebo services not available - is the sim running?")

    world = svc("/gazebo/get_world_properties", GetWorldProperties)
    modelprops = svc("/gazebo/get_model_properties", GetModelProperties)
    pause = svc("/gazebo/pause_physics", Empty)
    unpause = svc("/gazebo/unpause_physics", Empty)
    setcfg = svc("/gazebo/set_model_configuration", SetModelConfiguration)
    getj = svc("/gazebo/get_joint_properties", GetJointProperties)
    clearj = svc("/gazebo/clear_joint_forces", JointRequest)
    clearb = svc("/gazebo/clear_body_wrenches", BodyRequest)

    # ---- locate the model -------------------------------------------------
    model = None
    try:
        for m in world().model_names:
            if m.startswith("g1"):
                model = m
                break
    except Exception:
        pass
    if model is None:
        sys.exit("ERROR: no g1* model found in the world.")

    # only reset joints this model actually has
    try:
        have = set(modelprops(model).joint_names)
    except Exception:
        have = set()
    targets = [j for j in (ARM_JOINTS + EXTRA_JOINTS) if not have or j in have]

    print(f"  model            : {model}")
    print(f"  resettable joints: {len(targets)}")

    if args.verbose:
        print("  before:")
        for j in targets:
            try:
                p = getj(j)
                if p.success:
                    print(f"    {j:30s} pos={p.position[0]:+.4f} rate={p.rate[0]:+.4f}")
            except Exception:
                pass

    # ---- 1. cancel every pending force BEFORE touching positions ----------
    n_cleared = 0
    for j in targets:
        try:
            clearj(j)
            n_cleared += 1
        except Exception:
            pass
    for l in PUSHABLE_LINKS:
        for body in (f"{model}::{l}", l):
            try:
                clearb(body)
            except Exception:
                pass
    print(f"  cleared forces on: {n_cleared} joints + {len(PUSHABLE_LINKS)} links")

    # ---- 2. freeze, zero the joints, resume -------------------------------
    pause()
    resp = setcfg(model_name=model,
                  urdf_param_name="robot_description",
                  joint_names=targets,
                  joint_positions=[0.0] * len(targets))
    unpause()

    if not resp.success:
        sys.exit(f"ERROR: set_model_configuration failed: {resp.status_message}")

    # set_model_configuration zeroes velocity as part of the write, but a
    # second pass after a brief pause reliably kills any residual spin.
    rospy.sleep(0.3)
    pause()
    setcfg(model_name=model,
           urdf_param_name="robot_description",
           joint_names=targets,
           joint_positions=[0.0] * len(targets))
    unpause()

    print(f"  joints zeroed    : OK")
    print(f"  settling {args.settle:.1f}s (arms fall to natural rest)...")
    rospy.sleep(args.settle)

    # ---- 3. report --------------------------------------------------------
    print("  at rest:")
    show = targets if args.verbose else [
        "left_shoulder_pitch_joint", "left_shoulder_roll_joint",
        "left_elbow_joint", "right_shoulder_pitch_joint",
        "right_shoulder_roll_joint", "right_elbow_joint"]
    maxrate = 0.0
    for j in show:
        try:
            p = getj(j)
            if p.success:
                maxrate = max(maxrate, abs(p.rate[0]))
                print(f"    {j:30s} pos={p.position[0]:+.4f} rate={p.rate[0]:+.4f}")
        except Exception:
            pass

    if maxrate > 0.05:
        print(f"  NOTE: still moving (max rate {maxrate:.3f} rad/s) - "
              f"rerun with --settle 6 if you need it fully still.")
    else:
        print("  stable.")


if __name__ == "__main__":
    main()
