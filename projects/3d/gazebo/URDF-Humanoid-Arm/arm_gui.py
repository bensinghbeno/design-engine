#!/usr/bin/env python3
"""
Slider GUI for the upper arm's shoulder joint.

One slider, 0-360 degrees. 0 is straight down (gravity rest), and the angle
increases as the arm swings. Drag it and the arm moves live and stays put.

How the "hold" works
--------------------
The shoulder is a passive joint - no controller, no PID, nothing driving it.
Left alone the arm just falls and swings. To make a slider actually hold a
pose we re-assert the target angle at ~30 Hz through
/gazebo/set_model_configuration. Each call sets the position AND zeroes the
velocity, so the arm is driven kinematically to wherever the slider says and
stays there.

That also means this is a kinematic override, not a torque command. The arm
will happily be driven through the crossbar if you ask it to - there is no
force being applied and no contact resolution while the hold is running.

Buttons
-------
  Reset     snap back to 0 degrees (straight down).
  Release   stop holding and let the arm fall under gravity. The slider then
            follows the joint's real angle instead of driving it, so you can
            watch it swing and settle.

Run via 2-arm-gui.sh so the ROS environment is set up correctly.
"""
import sys
import threading

import rospy
from gazebo_msgs.srv import (GetWorldProperties, GetJointProperties,
                             SetModelConfiguration)

import tkinter as tk
from tkinter import ttk

import math

JOINT = "shoulder_joint"
DEFAULT_MODEL = "arm_rig"
HOLD_HZ = 30.0


def detect_model():
    """Find the spawned rig in the world, falling back to the usual name."""
    try:
        gwp = rospy.ServiceProxy("/gazebo/get_world_properties",
                                 GetWorldProperties)
        names = gwp().model_names
        if DEFAULT_MODEL in names:
            return DEFAULT_MODEL
        for name in names:
            if name not in ("ground_plane",):
                return name
    except Exception:
        pass
    return DEFAULT_MODEL


class ArmGui:
    def __init__(self, root):
        self.root = root
        self.model = detect_model()
        self.holding = True
        self.target_deg = 0.0
        self.lock = threading.Lock()

        self.setcfg = rospy.ServiceProxy("/gazebo/set_model_configuration",
                                         SetModelConfiguration)
        self.getj = rospy.ServiceProxy("/gazebo/get_joint_properties",
                                       GetJointProperties)

        self._build_ui()

        self.running = True
        self.thread = threading.Thread(target=self._hold_loop, daemon=True)
        self.thread.start()

        self._poll_actual()

    # ---------------- ui ----------------
    def _build_ui(self):
        self.root.title("Upper arm - shoulder angle")
        self.root.geometry("520x220")

        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=f"model: {self.model}   joint: {JOINT}",
                  foreground="#666").pack(anchor="w")

        row = ttk.Frame(frm)
        row.pack(fill="x", pady=(12, 0))

        ttk.Label(row, text="0", width=4).pack(side="left")
        self.scale = ttk.Scale(row, from_=0.0, to=360.0, orient="horizontal",
                               command=self._on_slide)
        self.scale.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Label(row, text="360", width=4).pack(side="left")

        self.value_lbl = ttk.Label(frm, text="target    0.0 deg",
                                   font=("TkDefaultFont", 13, "bold"))
        self.value_lbl.pack(anchor="w", pady=(10, 0))

        self.actual_lbl = ttk.Label(frm, text="actual    -- deg",
                                    foreground="#666")
        self.actual_lbl.pack(anchor="w")

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(14, 0))
        ttk.Button(btns, text="Reset", command=self.reset).pack(side="left")
        self.hold_btn = ttk.Button(btns, text="Release",
                                   command=self.toggle_hold)
        self.hold_btn.pack(side="left", padx=8)

        self.status = ttk.Label(frm, text="holding", foreground="#0a0")
        self.status.pack(side="left", padx=8)

    def _on_slide(self, raw):
        with self.lock:
            self.target_deg = float(raw)
            if not self.holding:
                # dragging the slider re-engages the hold
                self.holding = True
                self._set_status(True)
        self.value_lbl.config(text=f"target    {float(raw):6.1f} deg")

    def _set_status(self, holding):
        if holding:
            self.status.config(text="holding", foreground="#0a0")
            self.hold_btn.config(text="Release")
        else:
            self.status.config(text="free - falling under gravity",
                               foreground="#a60")
            self.hold_btn.config(text="Hold")

    def reset(self):
        self.scale.set(0.0)
        with self.lock:
            self.target_deg = 0.0
            self.holding = True
        self._set_status(True)

    def toggle_hold(self):
        with self.lock:
            self.holding = not self.holding
            holding = self.holding
        self._set_status(holding)

    # ---------------- gazebo ----------------
    def _hold_loop(self):
        """Re-assert the target angle continuously so the pose sticks."""
        rate = rospy.Rate(HOLD_HZ)
        while self.running and not rospy.is_shutdown():
            with self.lock:
                holding = self.holding
                deg = self.target_deg
            if holding:
                try:
                    self.setcfg(model_name=self.model,
                                urdf_param_name="robot_description",
                                joint_names=[JOINT],
                                joint_positions=[math.radians(deg)])
                except Exception:
                    pass
            try:
                rate.sleep()
            except Exception:
                break

    def _poll_actual(self):
        """Show the joint's real angle, and track it while released."""
        try:
            p = self.getj(JOINT)
            if p.success:
                deg = math.degrees(p.position[0]) % 360.0
                self.actual_lbl.config(text=f"actual    {deg:6.1f} deg")
                with self.lock:
                    free = not self.holding
                if free:
                    # follow the arm instead of driving it
                    self.scale.set(deg)
                    self.target_deg = deg
                    self.value_lbl.config(text=f"target    {deg:6.1f} deg")
        except Exception:
            self.actual_lbl.config(text="actual    -- deg (no sim?)")
        self.root.after(100, self._poll_actual)

    def shutdown(self):
        self.running = False


def main():
    rospy.init_node("arm_gui", anonymous=True, disable_signals=True)
    try:
        rospy.wait_for_service("/gazebo/set_model_configuration", timeout=10)
    except rospy.ROSException:
        sys.exit("ERROR: Gazebo services not available - is the sim running?")

    root = tk.Tk()
    gui = ArmGui(root)
    root.protocol("WM_DELETE_WINDOW",
                  lambda: (gui.shutdown(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
