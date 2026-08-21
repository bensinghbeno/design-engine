#!/usr/bin/env python3
"""
Interactive slider GUI for the Unitree G1 torso rig in Gazebo.

One horizontal slider per arm joint. The slider's centre is the joint's
current gravity-rest angle (arms hanging), so pushing left/right offsets the
joint symmetrically from that rest pose. Motion is applied live and held.

How the "hold" works
--------------------
The torso rig has no controllers - the arms just fall under gravity. To make a
slider actually hold a pose we re-assert every joint's target angle at ~30 Hz
through /gazebo/set_model_configuration (the same service the pose/wave modes
use). Each call sets the position and zeroes velocity, so the arm is driven
kinematically to wherever the sliders say and stays there, updating the instant
you drag a slider.

Buttons
-------
  Reset          snap every slider back to its captured rest centre.
  Recapture rest release the hold, let the arms fall to their true gravity
                 rest, then adopt that as the new slider centre (this is the
                 "default can be updated after launch" behaviour).

Run via g1-gui.sh so the ROS environment / Python are set up correctly.
"""
import os
import sys
import threading
import xml.etree.ElementTree as ET

import rospy
from gazebo_msgs.srv import (GetWorldProperties, GetJointProperties,
                             SetModelConfiguration)

import tkinter as tk
from tkinter import ttk

# The 14 movable arm joints of the torso rig, in a sensible top-to-bottom order.
ARM_JOINTS = [
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint", "left_elbow_joint",
    "left_wrist_roll_joint", "left_wrist_pitch_joint", "left_wrist_yaw_joint",
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint", "right_elbow_joint",
    "right_wrist_roll_joint", "right_wrist_pitch_joint", "right_wrist_yaw_joint",
]

HERE = os.path.dirname(os.path.abspath(__file__))
URDF = os.path.join(HERE, "urdf", "g1_torso.urdf")
HOLD_HZ = 30.0


def detect_model():
    try:
        gwp = rospy.ServiceProxy('/gazebo/get_world_properties', GetWorldProperties)
        for name in gwp().model_names:
            if name.startswith('g1'):
                return name
    except Exception:
        pass
    return 'g1_torso'


def read_limits():
    """joint_name -> (lower, upper) parsed from the torso URDF."""
    limits = {}
    try:
        root = ET.parse(URDF).getroot()
        for joint in root.findall('joint'):
            name = joint.get('name')
            lim = joint.find('limit')
            if name in ARM_JOINTS and lim is not None:
                limits[name] = (float(lim.get('lower', -3.14)),
                                float(lim.get('upper', 3.14)))
    except Exception as exc:
        print(f"[g1_gui] could not parse limits from {URDF}: {exc}")
    for j in ARM_JOINTS:
        limits.setdefault(j, (-3.14, 3.14))
    return limits


class G1Gui:
    def __init__(self):
        rospy.init_node('g1_gui', anonymous=True, disable_signals=True)
        rospy.wait_for_service('/gazebo/set_model_configuration', timeout=10)
        self.model = detect_model()
        self.limits = read_limits()

        self.get_joint = rospy.ServiceProxy('/gazebo/get_joint_properties',
                                            GetJointProperties)
        self.set_cfg = rospy.ServiceProxy('/gazebo/set_model_configuration',
                                          SetModelConfiguration)

        # centre[j] = captured rest angle; target[j] = commanded angle.
        self.center = {j: self.read_joint(j) for j in ARM_JOINTS}
        self.target = dict(self.center)

        self._lock = threading.Lock()
        self._holding = True
        self._stop = False

        self.build_ui()

        self.hold_thread = threading.Thread(target=self.hold_loop, daemon=True)
        self.hold_thread.start()

    # ---- ROS helpers ----------------------------------------------------
    def read_joint(self, joint):
        try:
            resp = self.get_joint(joint)
            if resp.position:
                return float(resp.position[0])
        except Exception:
            pass
        return 0.0

    def assert_pose(self):
        with self._lock:
            names = list(ARM_JOINTS)
            pos = [self.target[j] for j in names]
        try:
            self.set_cfg(self.model, 'robot_description', names, pos)
        except Exception:
            pass

    def hold_loop(self):
        period = 1.0 / HOLD_HZ
        while not self._stop:
            if self._holding:
                self.assert_pose()
            rospy.sleep(period)

    # ---- UI -------------------------------------------------------------
    def build_ui(self):
        self.root = tk.Tk()
        self.root.title(f"G1 joint control  [{self.model}]")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        head = ttk.Frame(self.root, padding=(10, 8))
        head.pack(fill='x')
        ttk.Label(head, text="Drag a slider - centre = gravity rest. "
                             "Live-held via set_model_configuration.",
                  font=('TkDefaultFont', 9)).pack(side='left')

        body = ttk.Frame(self.root, padding=(10, 4))
        body.pack(fill='both', expand=True)

        self.scales = {}
        self.value_lbls = {}
        for row, j in enumerate(ARM_JOINTS):
            lo, hi = self.limits[j]
            c = self.center[j]
            # Symmetric range about the rest centre, clamped to joint limits.
            span = min(c - lo, hi - c)
            span = max(span, 0.05)
            smin, smax = c - span, c + span

            ttk.Label(body, text=j, width=26, anchor='w').grid(
                row=row, column=0, sticky='w', pady=2)

            var = tk.DoubleVar(value=c)
            scale = tk.Scale(body, from_=smin, to=smax, resolution=0.005,
                             orient='horizontal', length=340, showvalue=0,
                             variable=var,
                             command=lambda v, jn=j: self.on_slide(jn, v))
            scale.grid(row=row, column=1, sticky='ew', padx=6)
            self.scales[j] = (scale, var)

            lbl = ttk.Label(body, text=f"{c:+.3f}", width=8, anchor='e')
            lbl.grid(row=row, column=2, sticky='e')
            self.value_lbls[j] = lbl

        body.columnconfigure(1, weight=1)

        foot = ttk.Frame(self.root, padding=(10, 8))
        foot.pack(fill='x')
        ttk.Button(foot, text="Reset to rest",
                   command=self.on_reset).pack(side='left')
        ttk.Button(foot, text="Recapture rest (let arms fall)",
                   command=self.on_recapture).pack(side='left', padx=8)
        self.status = ttk.Label(foot, text="holding", anchor='e')
        self.status.pack(side='right')

    def on_slide(self, joint, value):
        v = float(value)
        with self._lock:
            self.target[joint] = v
        self.value_lbls[joint].config(text=f"{v:+.3f}")

    def on_reset(self):
        for j in ARM_JOINTS:
            scale, var = self.scales[j]
            var.set(self.center[j])
            with self._lock:
                self.target[j] = self.center[j]
            self.value_lbls[j].config(text=f"{self.center[j]:+.3f}")
        self.status.config(text="reset to rest")

    def on_recapture(self):
        """Stop holding, let gravity settle the arms, then adopt as new centre."""
        self.status.config(text="recapturing... (2s)")
        self.root.update_idletasks()
        self._holding = False

        def worker():
            rospy.sleep(2.0)                     # let the arms fall to rest
            for j in ARM_JOINTS:
                self.center[j] = self.read_joint(j)
            with self._lock:
                self.target = dict(self.center)
            self._holding = True
            self.root.after(0, self.rebuild_centers)

        threading.Thread(target=worker, daemon=True).start()

    def rebuild_centers(self):
        for j in ARM_JOINTS:
            lo, hi = self.limits[j]
            c = self.center[j]
            span = max(min(c - lo, hi - c), 0.05)
            scale, var = self.scales[j]
            scale.config(from_=c - span, to=c + span)
            var.set(c)
            self.value_lbls[j].config(text=f"{c:+.3f}")
        self.status.config(text="rest updated - holding")

    def on_close(self):
        self._stop = True
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    try:
        G1Gui().run()
    except rospy.ROSException as exc:
        print(f"[g1_gui] {exc}\nIs Gazebo running? Launch with bash launch-g1-torso.sh")
        sys.exit(1)
