#!/usr/bin/env python3
"""Centered yaw and pitch sliders for the rig's two-axis shoulder.

Both sliders span -180..+180 degrees. Yaw rotates the whole pitch mount
about vertical Z; pitch rotates the arm about the mount's local Y.
The pair of target angles is reasserted together at approximately 30 Hz
through /gazebo/set_model_configuration. This is kinematic positioning,
not a torque controller or a collision-safe motion planner.

Reset centres both sliders. Release stops positioning both joints and
tracks their measured angles; dragging either slider re-engages Hold.
ROS calls run on a worker; only the main thread accesses Tk widgets.
Run via 1-launch-rig.sh or, with Gazebo already running, 2-arm-gui.sh.
"""
import sys
import threading

import rospy
from gazebo_msgs.srv import (GetWorldProperties, GetJointProperties,
                             SetModelConfiguration)

import tkinter as tk
from tkinter import ttk

import math

JOINTS = (
    ("shoulder_yaw_joint", "Yaw · vertical Z (blue)"),
    ("shoulder_joint", "Pitch · local Y (green)"),
)
DEFAULT_MODEL = "arm_rig"
HOLD_HZ = 30.0

# Slider spans a full turn centred on 0 (straight down).
ANGLE_MIN = -180.0
ANGLE_MAX = 180.0


def wrap180(deg):
    """Fold an angle into -180..+180 so it lands on the slider's scale."""
    return (deg + 180.0) % 360.0 - 180.0


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
        self.target_deg = {name: 0.0 for name, _ in JOINTS}
        self.actual_deg = {name: None for name, _ in JOINTS}
        self.service_error = ""
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.running = True
        self.scales = {}
        self.scale_vars = {}
        self.value_labels = {}
        self.actual_labels = {}

        self.setcfg = rospy.ServiceProxy("/gazebo/set_model_configuration",
                                         SetModelConfiguration)
        self.getj = rospy.ServiceProxy("/gazebo/get_joint_properties",
                                       GetJointProperties)

        self._build_ui()

        self.thread = threading.Thread(target=self._hold_loop, daemon=True)
        self.thread.start()

        self._poll_actual()

    # ---------------- ui ----------------
    def _build_ui(self):
        self.root.title("Upper arm - yaw and pitch")
        self.root.geometry("600x440")
        self.root.minsize(520, 420)

        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=f"model: {self.model}   |   yaw → pitch",
                  foreground="#666").pack(anchor="w")
        for name, title in JOINTS:
            group = ttk.LabelFrame(frm, text=title, padding=10)
            group.pack(fill="x", pady=(12, 0))
            row = ttk.Frame(group)
            row.pack(fill="x")
            ttk.Label(row, text="-180", width=5).pack(side="left")
            # Setting the variable (instead of Scale.set) does not invoke
            # the drag callback, so feedback cannot accidentally enable Hold.
            variable = tk.DoubleVar(master=self.root, value=0.0)
            scale = ttk.Scale(row, from_=ANGLE_MIN, to=ANGLE_MAX,
                              variable=variable, orient="horizontal",
                              command=lambda raw, joint=name: self._on_slide(joint, raw))
            scale.pack(side="left", fill="x", expand=True, padx=6)
            ttk.Label(row, text="+180", width=5).pack(side="left")
            ticks = ttk.Frame(group)
            ticks.pack(fill="x", padx=42)
            for column, text in enumerate(("-180", "-90", "0", "+90", "+180")):
                ticks.columnconfigure(column, weight=1, uniform="ticks")
                ttk.Label(ticks, text=text, foreground="#888").grid(row=0, column=column)
            target = ttk.Label(group, text="target    +0.0 deg",
                               font=("TkDefaultFont", 12, "bold"))
            target.pack(anchor="w", pady=(5, 0))
            actual = ttk.Label(group, text="actual    -- deg", foreground="#666")
            actual.pack(anchor="w")
            self.scales[name] = scale
            self.scale_vars[name] = variable
            self.value_labels[name] = target
            self.actual_labels[name] = actual

        ttk.Label(frm, text="Yaw turns the pitch actuator; pitch turns the arm.",
                  foreground="#666").pack(anchor="w", pady=(8, 0))

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(14, 0))
        ttk.Button(btns, text="Reset both", command=self.reset).pack(side="left")
        self.hold_btn = ttk.Button(btns, text="Release",
                                   command=self.toggle_hold)
        self.hold_btn.pack(side="left", padx=8)

        self.status = ttk.Label(frm, text="holding both joints", foreground="#0a0",
                                wraplength=540)
        self.status.pack(anchor="w", pady=(8, 0))

    def _on_slide(self, joint, raw):
        with self.lock:
            self.target_deg[joint] = float(raw)
            self.holding = True
        self._set_status(True)
        self.value_labels[joint].config(text=f"target    {float(raw):+6.1f} deg")

    def _set_status(self, holding):
        if holding:
            self.status.config(text="holding both joints", foreground="#0a0")
            self.hold_btn.config(text="Release")
        else:
            self.status.config(text="free - falling under gravity",
                               foreground="#a60")
            self.hold_btn.config(text="Hold")

    def reset(self):
        with self.lock:
            self.target_deg = {name: 0.0 for name, _ in JOINTS}
            self.holding = True
        for name, _ in JOINTS:
            self.scale_vars[name].set(0.0)
            self.value_labels[name].config(text="target    +0.0 deg")
        self._set_status(True)

    def toggle_hold(self):
        with self.lock:
            self.holding = not self.holding
            holding = self.holding
        self._set_status(holding)

    # ---------------- gazebo ----------------
    def _hold_loop(self):
        """Command both joints together and publish feedback to the UI cache."""
        names = [name for name, _ in JOINTS]
        while not self.stop_event.is_set() and not rospy.is_shutdown():
            with self.lock:
                holding = self.holding
                positions = [math.radians(self.target_deg[name]) for name in names]
            error = ""
            if holding:
                try:
                    response = self.setcfg(model_name=self.model,
                                           urdf_param_name="robot_description",
                                           joint_names=names,
                                           joint_positions=positions)
                    if not response.success:
                        error = response.status_message or "Joint command rejected. Restart the rig with yaw enabled."
                except Exception as exc:
                    error = f"Gazebo command unavailable: {exc}"
            actual = {}
            for name in names:
                try:
                    response = self.getj(f"{self.model}::{name}")
                    actual[name] = (wrap180(math.degrees(response.position[0]))
                                    if response.success and response.position else None)
                except Exception:
                    actual[name] = None
            if any(value is None for value in actual.values()) and not error:
                error = "Joint feedback unavailable. Restart the rig if yaw was just added."
            with self.lock:
                self.actual_deg = actual
                self.service_error = error
            # Wall time avoids hanging on a paused simulation clock.
            self.stop_event.wait(1.0 / HOLD_HZ)

    def _poll_actual(self):
        """Main-thread Tk updates only; no blocking ROS calls here."""
        if not self.running:
            return
        with self.lock:
            actual = self.actual_deg.copy()
            holding = self.holding
            error = self.service_error
            if not holding:
                self.target_deg.update({name: deg for name, deg in actual.items() if deg is not None})
        for name, deg in actual.items():
            text = "actual    -- deg (no feedback)" if deg is None else f"actual    {deg:+6.1f} deg"
            self.actual_labels[name].config(text=text)
            if not holding and deg is not None:
                self.scale_vars[name].set(deg)
                self.value_labels[name].config(text=f"target    {deg:+6.1f} deg")
        self._set_status(holding)
        if error:
            self.status.config(text=error, foreground="#a60")
        self.poll_id = self.root.after(100, self._poll_actual)

    def shutdown(self):
        self.running = False
        self.stop_event.set()
        if hasattr(self, "poll_id"):
            self.root.after_cancel(self.poll_id)
        self.thread.join(timeout=1.0)


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
