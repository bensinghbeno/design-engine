#!/usr/bin/env python3
"""Seven centered arm controls and one 0..80 mm gripper aperture control.

G1-style order: shoulder pitch/roll/yaw, elbow, wrist roll/pitch/yaw.
All arm sliders span -180..+180 degrees (not the G1's real travel limits).
The seven angles and two independent finger positions are reasserted in
one /gazebo/set_model_configuration call at approximately 30 Hz. Each
finger travels half the aperture, 0..0.04 m, along opposite local Y axes.
This is kinematic positioning, not torque control or collision-safe motion.

Reset centres the arm and closes the gripper. Release stops positioning
all nine joints and tracks feedback; dragging any control re-engages Hold.
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
    ("shoulder_joint", "1 · Shoulder pitch · Y · purple"),
    ("shoulder_roll_joint", "2 · Shoulder roll · X · green"),
    ("shoulder_yaw_joint", "3 · Shoulder yaw / twist · Z · cyan"),
    ("elbow_joint", "4 · Elbow · local Y"),
    ("wrist_roll_joint", "5 · Wrist roll · X along forearm"),
    ("wrist_pitch_joint", "6 · Wrist pitch · local Y"),
    ("wrist_yaw_joint", "7 · Wrist yaw · local Z"),
)
GRIPPER_JOINTS = ("gripper_left_joint", "gripper_right_joint")
PHYSICAL_JOINTS = tuple(name for name, _ in JOINTS) + GRIPPER_JOINTS
JOINT_COLOURS = ("#8033aa", "#237a35", "#087e91", "#a34c13",
                 "#315fa3", "#a33c6b", "#526576")
APERTURE_MAX_MM = 80.0
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
        self.target_aperture_mm = 0.0
        self.actual_aperture_mm = None
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
        self.root.title("G1-order arm · 7 joints + gripper")
        self.root.geometry("880x740")
        self.root.minsize(800, 710)

        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=f"model: {self.model}   |   shoulder → elbow → wrist → gripper",
                  foreground="#666").pack(anchor="w")
        controls = ttk.Frame(frm)
        controls.pack(fill="both", expand=True, pady=(6, 0))
        for column in range(2):
            controls.columnconfigure(column, weight=1, uniform="controls")
        for index, (name, title) in enumerate(JOINTS):
            group = ttk.LabelFrame(controls, padding=8)
            heading = ttk.Label(group, text=title, foreground=JOINT_COLOURS[index])
            group.configure(labelwidget=heading)
            group.grid(row=index % 4, column=index // 4, sticky="nsew", padx=4, pady=4)
            controls.rowconfigure(index % 4, weight=1)
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

        group = ttk.LabelFrame(controls, text="8 · Gripper · full aperture", padding=8)
        group.grid(row=3, column=1, sticky="nsew", padx=4, pady=4)
        row = ttk.Frame(group)
        row.pack(fill="x")
        ttk.Label(row, text="0 mm", width=5).pack(side="left")
        self.aperture_var = tk.DoubleVar(master=self.root, value=0.0)
        self.aperture_scale = ttk.Scale(
            row, from_=0.0, to=APERTURE_MAX_MM, variable=self.aperture_var,
            orient="horizontal", command=self._on_aperture_slide)
        self.aperture_scale.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Label(row, text="80 mm", width=6).pack(side="left")
        ttk.Label(group, text="Closed ←   two fingers together   → Open",
                  foreground="#666").pack(anchor="w")
        self.aperture_target_label = ttk.Label(
            group, text="target     0.0 mm", font=("TkDefaultFont", 12, "bold"))
        self.aperture_target_label.pack(anchor="w", pady=(5, 0))
        self.aperture_actual_label = ttk.Label(group, text="actual    -- mm", foreground="#666")
        self.aperture_actual_label.pack(anchor="w")

        ttk.Label(frm, text="Kinematic hold · not collision-safe. Release tracks feedback; drag any control to hold.",
                  foreground="#666").pack(anchor="w", pady=(6, 0))

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(14, 0))
        ttk.Button(btns, text="Reset all", command=self.reset).pack(side="left")
        self.hold_btn = ttk.Button(btns, text="Release",
                                   command=self.toggle_hold)
        self.hold_btn.pack(side="left", padx=8)

        self.status = ttk.Label(frm, text="holding arm + gripper", foreground="#0a0",
                    wraplength=760)
        self.status.pack(anchor="w", pady=(8, 0))

    def _on_slide(self, joint, raw):
        with self.lock:
            self.target_deg[joint] = float(raw)
            self.holding = True
        self._set_status(True)
        self.value_labels[joint].config(text=f"target    {float(raw):+6.1f} deg")

    def _on_aperture_slide(self, raw):
        aperture = max(0.0, min(APERTURE_MAX_MM, float(raw)))
        with self.lock:
            self.target_aperture_mm = aperture
            self.holding = True
        self._set_status(True)
        self.aperture_target_label.config(text=f"target    {aperture:5.1f} mm")

    def _set_status(self, holding):
        if holding:
            self.status.config(text="holding arm + gripper", foreground="#0a0")
            self.hold_btn.config(text="Release")
        else:
            self.status.config(text="free - falling under gravity",
                               foreground="#a60")
            self.hold_btn.config(text="Hold")

    def reset(self):
        with self.lock:
            self.target_deg = {name: 0.0 for name, _ in JOINTS}
            self.target_aperture_mm = 0.0
            self.holding = True
        for name, _ in JOINTS:
            self.scale_vars[name].set(0.0)
            self.value_labels[name].config(text="target    +0.0 deg")
        self.aperture_var.set(0.0)
        self.aperture_target_label.config(text="target     0.0 mm")
        self._set_status(True)

    def toggle_hold(self):
        with self.lock:
            self.holding = not self.holding
            holding = self.holding
        self._set_status(holding)

    # ---------------- gazebo ----------------
    def _hold_loop(self):
        """Command all joints together and publish feedback to the UI cache."""
        names = list(PHYSICAL_JOINTS)
        while not self.stop_event.is_set() and not rospy.is_shutdown():
            with self.lock:
                holding = self.holding
                positions = [math.radians(self.target_deg[name]) for name, _ in JOINTS]
                # Full aperture mm -> half aperture metres per physical finger.
                positions.extend([self.target_aperture_mm / 2000.0] * 2)
            error = ""
            if holding:
                try:
                    response = self.setcfg(model_name=self.model,
                                           urdf_param_name="robot_description",
                                           joint_names=names,
                                           joint_positions=positions)
                    if not response.success:
                        error = response.status_message or "Joint command rejected. Restart the rig with all 7 arm joints and 2 fingers."
                except Exception as exc:
                    error = f"Gazebo command unavailable: {exc}"
            measured = {}
            for name in names:
                try:
                    response = self.getj(f"{self.model}::{name}")
                    value = response.position[0] if response.success and response.position else None
                    if value is None or not math.isfinite(value):
                        detail = getattr(response, "status_message", "") or "missing or invalid position"
                        raise ValueError(detail)
                    measured[name] = value
                except Exception as exc:
                    measured[name] = None
                    if not error:
                        error = f"Joint feedback unavailable ({name}): {exc}"
            actual = {name: (wrap180(math.degrees(measured[name]))
                             if measured[name] is not None else None) for name, _ in JOINTS}
            fingers = [measured[name] for name in GRIPPER_JOINTS]
            aperture = sum(fingers) * 1000.0 if all(value is not None for value in fingers) else None
            with self.lock:
                self.actual_deg = actual
                self.actual_aperture_mm = aperture
                self.service_error = error
            # Wall time avoids hanging on a paused simulation clock.
            self.stop_event.wait(1.0 / HOLD_HZ)

    def _poll_actual(self):
        """Main-thread Tk updates only; no blocking ROS calls here."""
        if not self.running:
            return
        with self.lock:
            actual = self.actual_deg.copy()
            aperture = self.actual_aperture_mm
            holding = self.holding
            error = self.service_error
            if not holding:
                self.target_deg.update({name: deg for name, deg in actual.items() if deg is not None})
                if aperture is not None:
                    # Preserve raw actual feedback, but never command beyond travel.
                    self.target_aperture_mm = max(0.0, min(APERTURE_MAX_MM, aperture))
            target_aperture = self.target_aperture_mm
        for name, deg in actual.items():
            text = "actual    -- deg (no feedback)" if deg is None else f"actual    {deg:+6.1f} deg"
            self.actual_labels[name].config(text=text)
            if not holding and deg is not None:
                self.scale_vars[name].set(deg)
                self.value_labels[name].config(text=f"target    {deg:+6.1f} deg")
        self.aperture_actual_label.config(
            text="actual    -- mm (no feedback)" if aperture is None else f"actual    {aperture:5.1f} mm")
        if not holding and aperture is not None:
            # DoubleVar.set never invokes the Scale command: stay released.
            self.aperture_var.set(target_aperture)
            self.aperture_target_label.config(text=f"target    {target_aperture:5.1f} mm")
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
