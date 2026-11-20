"""Four-joint kinematic Gazebo controls for Rig 2; no hardware commands."""

import math
from pathlib import Path
import threading
import tkinter as tk
from tkinter import ttk
import xml.etree.ElementTree as ET

MODEL = "rig2_servo_arm"
JOINTS = (
    ("shoulder_joint", "Shoulder pitch - RobStride"),
    ("shoulder_roll_joint", "Shoulder roll"),
    ("elbow_joint", "Elbow"),
    ("wrist_roll_joint", "Wrist roll"),
)


def joint_limits():
    robot = ET.parse(Path(__file__).resolve().parents[1] / "urdf/rig2.urdf").getroot()
    result = {}
    for name, _ in JOINTS:
        joint = robot.find(f"joint[@name='{name}']")
        if joint.attrib["type"] == "continuous":
            result[name] = (-180.0, 180.0)
        else:
            limit = joint.find("limit")
            result[name] = tuple(math.degrees(float(limit.attrib[key])) for key in ("lower", "upper"))
    return result


class Rig2Gui:
    def __init__(self, root, set_configuration, get_joint, is_shutdown):
        self.root = root
        self.set_configuration = set_configuration
        self.get_joint = get_joint
        self.is_shutdown = is_shutdown
        self.limits = joint_limits()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.holding = False
        self.target = {name: 0.0 for name, _ in JOINTS}
        self.actual = {name: None for name, _ in JOINTS}
        self.error = "Waiting for Rig 2 feedback"
        self.variables = {}
        self.labels = {}
        self.scales = {}
        root.title("Rig 2 - four-joint Gazebo control")
        root.geometry("800x430")
        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)
        for column in range(2):
            frame.columnconfigure(column, weight=1)
        for index, (name, title) in enumerate(JOINTS):
            group = ttk.LabelFrame(frame, text=title, padding=10)
            group.grid(row=index // 2, column=index % 2, sticky="nsew", padx=5, pady=5)
            frame.rowconfigure(index // 2, weight=1)
            lower, upper = self.limits[name]
            ttk.Label(group, text=f"{lower:g} to {upper:g} deg").pack(anchor="w")
            variable = tk.DoubleVar(master=root)
            scale = ttk.Scale(group, from_=lower, to=upper, variable=variable,
                              command=lambda raw, joint=name: self.slide(joint, raw))
            scale.pack(fill="x", pady=12)
            scale.state(["disabled"])
            label = ttk.Label(group, text="Waiting for feedback")
            label.pack(anchor="w")
            self.variables[name], self.labels[name], self.scales[name] = variable, label, scale
        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
        self.hold_button = ttk.Button(buttons, text="Hold", command=self.toggle_hold)
        self.hold_button.pack(side="left")
        self.reset_button = ttk.Button(buttons, text="Reset to zero", command=self.reset)
        self.reset_button.pack(side="left", padx=10)
        self.status = ttk.Label(frame, wraplength=730)
        self.status.grid(row=3, column=0, columnspan=2, sticky="w")
        self.thread = threading.Thread(target=self.worker, daemon=True)
        self.thread.start()
        self.poll()

    def ready(self):
        return all(value is not None for value in self.actual.values()) and not self.error

    def slide(self, name, raw):
        with self.lock:
            if not self.ready():
                return
            lower, upper = self.limits[name]
            self.target[name] = max(lower, min(upper, float(raw)))
            self.holding = True

    def toggle_hold(self):
        with self.lock:
            if self.holding or self.ready():
                self.holding = not self.holding

    def reset(self):
        with self.lock:
            if self.ready():
                self.target = {name: 0.0 for name, _ in JOINTS}
                self.holding = True

    def cycle(self):
        with self.lock:
            holding, targets = self.holding, self.target.copy()
        error = ""
        if holding:
            try:
                reply = self.set_configuration(
                    model_name=MODEL, urdf_param_name="robot_description",
                    joint_names=[name for name, _ in JOINTS],
                    joint_positions=[math.radians(targets[name]) for name, _ in JOINTS])
                if not reply.success:
                    raise RuntimeError(reply.status_message or "Rig 2 joint command rejected")
            except Exception as exception:
                error = str(exception)
        actual = {}
        for name, _ in JOINTS:
            try:
                reply = self.get_joint(f"{MODEL}::{name}")
                if not reply.success or not reply.position or not math.isfinite(reply.position[0]):
                    raise RuntimeError(f"Missing Rig 2 feedback: {name}")
                degrees = math.degrees(reply.position[0])
                actual[name] = (degrees + 180) % 360 - 180 if name == "shoulder_joint" else degrees
            except Exception as exception:
                actual[name] = None
                error = error or str(exception)
        with self.lock:
            self.actual, self.error = actual, error
            if error:
                self.holding = False
            if not self.holding:
                for name, value in actual.items():
                    if value is not None:
                        lower, upper = self.limits[name]
                        self.target[name] = max(lower, min(upper, value))

    def worker(self):
        while not self.stop_event.is_set() and not self.is_shutdown():
            self.cycle()
            self.stop_event.wait(1 / 30)

    def poll(self):
        if self.stop_event.is_set():
            return
        with self.lock:
            actual, target = self.actual.copy(), self.target.copy()
            holding, error, ready = self.holding, self.error, self.ready()
        for name, _ in JOINTS:
            self.variables[name].set(target[name])
            self.scales[name].state(["!disabled" if ready else "disabled"])
            measured = "--" if actual[name] is None else f"{actual[name]:+.1f}"
            self.labels[name].configure(text=f"Target {target[name]:+.1f} deg | Actual {measured} deg")
        self.hold_button.configure(text="Release" if holding else "Hold")
        self.hold_button.state(["!disabled" if ready or holding else "disabled"])
        self.reset_button.state(["!disabled" if ready else "disabled"])
        self.status.configure(text=error or ("Kinematic hold - not collision-safe" if holding
                                           else "Released - simulation can fall when unpaused"))
        self.poll_id = self.root.after(100, self.poll)

    def shutdown(self):
        self.stop_event.set()
        self.root.after_cancel(self.poll_id)
        self.thread.join(timeout=1)


def main():
    import rospy
    from gazebo_msgs.srv import GetJointProperties, GetWorldProperties, SetModelConfiguration

    rospy.init_node("rig2_arm_gui", anonymous=True, disable_signals=True)
    for service in ("set_model_configuration", "get_joint_properties", "get_world_properties"):
        rospy.wait_for_service(f"/gazebo/{service}", timeout=10)
    world = rospy.ServiceProxy("/gazebo/get_world_properties", GetWorldProperties)()
    if MODEL not in world.model_names:
        raise SystemExit("Rig 2 is not spawned. Run bash rig2/1-launch-rig.sh first.")
    root = tk.Tk()
    gui = Rig2Gui(root, rospy.ServiceProxy("/gazebo/set_model_configuration", SetModelConfiguration),
                  rospy.ServiceProxy("/gazebo/get_joint_properties", GetJointProperties), rospy.is_shutdown)
    root.protocol("WM_DELETE_WINDOW", lambda: (gui.shutdown(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()