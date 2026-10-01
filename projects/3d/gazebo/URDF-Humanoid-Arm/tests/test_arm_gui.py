"""Real Tk widgets with mocked Gazebo services; run under a display or Xvfb."""
import importlib.util
import math
import os
from pathlib import Path
import subprocess
import sys
import threading
import tkinter as tk
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from xml.etree import ElementTree


ARM_NAMES = ["shoulder_joint", "shoulder_roll_joint", "elbow_joint", "wrist_roll_joint"]
FINGER_NAMES = ["gripper_left_joint", "gripper_right_joint"]
PHYSICAL_NAMES = ARM_NAMES + FINGER_NAMES
REMOVED_NAMES = {"shoulder_yaw_joint", "wrist_pitch_joint", "wrist_yaw_joint"}


rospy = ModuleType("rospy")
rospy.is_shutdown = Mock(return_value=False)
rospy.ServiceProxy = Mock()
services = ModuleType("gazebo_msgs.srv")
for name in ("GetWorldProperties", "GetJointProperties", "SetModelConfiguration"):
    setattr(services, name, type(name, (), {}))
spec = importlib.util.spec_from_file_location(
    "arm_gui", Path(__file__).resolve().parents[1] / "arm_gui.py")
gui_module = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"rospy": rospy, "gazebo_msgs": ModuleType("gazebo_msgs"),
                             "gazebo_msgs.srv": services}):
    spec.loader.exec_module(gui_module)


class ArmGuiTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.setcfg = Mock(return_value=SimpleNamespace(success=True, status_message=""))
        self.getj = Mock(return_value=SimpleNamespace(success=True, position=[0.0]))
        rospy.ServiceProxy.side_effect = lambda name, kind: (
            self.setcfg if name.endswith("set_model_configuration") else self.getj)
        # Keep execution deterministic; worker code is exercised separately.
        with patch.object(gui_module, "detect_model", return_value="arm_rig"), \
                patch.object(gui_module.threading, "Thread"):
            self.gui = gui_module.ArmGui(self.root)
        self.names = [name for name, _ in gui_module.JOINTS]
        self.pitch, self.roll, self.elbow, self.wrist = self.names

    def tearDown(self):
        self.gui.shutdown()
        # Drain pending ttk theme/layout events before destroying this Tcl
        # interpreter; otherwise later tests can emit stale ThemeChanged errors.
        self.root.update_idletasks()
        self.root.destroy()

    def poll(self):
        self.root.after_cancel(self.gui.poll_id)
        self.gui._poll_actual()

    def worker_once(self):
        self.gui.stop_event.clear()
        with patch.object(self.gui.stop_event, "wait", side_effect=lambda _: self.gui.stop_event.set()):
            self.gui._hold_loop()

    def test_sliders_start_centered_and_independent(self):
        self.assertEqual(self.names, ARM_NAMES)
        self.assertEqual(list(gui_module.PHYSICAL_JOINTS), PHYSICAL_NAMES)
        self.assertEqual(len(gui_module.JOINT_COLOURS), 4)
        self.assertTrue(REMOVED_NAMES.isdisjoint(self.gui.scales))
        self.assertTrue(REMOVED_NAMES.isdisjoint(gui_module.PHYSICAL_JOINTS))
        for name in self.names:
            scale = self.gui.scales[name]
            self.assertEqual(float(scale["from"]), -180)
            self.assertEqual(float(scale["to"]), 180)
            self.assertEqual(scale.get(), 0)
        expected = dict.fromkeys(self.names, 0)
        self.gui.scales[self.elbow].set(90)
        self.gui.scales[self.pitch].set(-45)
        expected.update({self.elbow: 90, self.pitch: -45})
        self.assertEqual(self.gui.target_deg, expected)
        self.gui.scales[self.roll].set(30)
        expected[self.roll] = 30
        self.assertEqual(self.gui.target_deg, expected)
        for index, name in enumerate(self.names[3:]):
            self.gui.scales[name].set(15 * (index + 1))
            expected[name] = 15 * (index + 1)
            self.assertEqual(self.gui.target_deg, expected)
        self.assertEqual(self.gui.target_aperture_mm, 0)

    def test_one_aperture_control_starts_closed(self):
        self.assertEqual(float(self.gui.aperture_scale["from"]), 0)
        self.assertEqual(float(self.gui.aperture_scale["to"]), 80)
        self.assertEqual(self.gui.aperture_scale.get(), 0)
        self.assertEqual(len(self.gui.scales), 4)
        self.gui.aperture_scale.set(60)
        self.assertEqual(self.gui.target_aperture_mm, 60)
        self.assertIn("60.0 mm", self.gui.aperture_target_label["text"])
        self.assertEqual(self.gui.target_deg, dict.fromkeys(self.names, 0))

    def test_worker_commands_six_joints_together_and_reads_scoped_names(self):
        degrees = [-45, 30, -60, 120]
        for name, angle in zip(self.names, degrees):
            self.gui.scales[name].set(angle)
        self.gui.aperture_scale.set(60)
        self.worker_once()
        self.setcfg.assert_called_once_with(
            model_name="arm_rig", urdf_param_name="robot_description",
            joint_names=PHYSICAL_NAMES,
            joint_positions=[math.radians(angle) for angle in degrees] + [0.03, 0.03])
        self.assertEqual([call.args[0] for call in self.getj.call_args_list],
                         ["arm_rig::" + name for name in PHYSICAL_NAMES])

    def test_aperture_command_conversions_and_limits(self):
        for aperture, travel in [(0, 0), (1, 0.0005), (40, 0.02), (80, 0.04),
                                  (-10, 0), (100, 0.04)]:
            with self.subTest(aperture=aperture):
                self.gui.aperture_scale.set(aperture)
                self.worker_once()
                positions = self.setcfg.call_args.kwargs["joint_positions"]
                self.assertEqual(positions, [0.0] * 4 + [travel, travel])

    def test_reset_all_and_reengage_hold(self):
        for scale in self.gui.scales.values():
            scale.set(65)
        self.gui.aperture_scale.set(80)
        self.gui.toggle_hold()
        self.gui.reset()
        self.assertTrue(self.gui.holding)
        self.assertEqual(self.gui.target_deg, dict.fromkeys(self.names, 0))
        self.assertTrue(all(scale.get() == 0 for scale in self.gui.scales.values()))
        self.assertEqual(self.gui.target_aperture_mm, 0)
        self.assertEqual(self.gui.aperture_scale.get(), 0)
        self.worker_once()
        self.setcfg.assert_called_once_with(
            model_name="arm_rig", urdf_param_name="robot_description",
            joint_names=PHYSICAL_NAMES, joint_positions=[0.0] * 6)

    def test_release_tracks_all_without_reholding(self):
        self.gui.toggle_hold()
        degrees = [-90, 45, -30, 120]
        positions = dict(zip(PHYSICAL_NAMES, [math.radians(d) for d in degrees] + [0.01, 0.025]))
        self.getj.side_effect = lambda name: SimpleNamespace(
            success=True, position=[positions[name.split("::")[-1]]])
        for _ in range(3):
            self.worker_once()
            self.poll()
            self.root.update_idletasks()
            self.assertFalse(self.gui.holding)
            for name, angle in zip(self.names, degrees):
                self.assertAlmostEqual(self.gui.scales[name].get(), angle)
                self.assertAlmostEqual(self.gui.target_deg[name], angle)
            # Sum both physical positions, not twice one finger's position.
            self.assertAlmostEqual(self.gui.aperture_scale.get(), 35)
            self.assertIn("35.0 mm", self.gui.aperture_actual_label["text"])
        self.setcfg.assert_not_called()
        self.assertEqual(self.gui.hold_btn["text"], "Hold")
        # Dragging elbow re-holds with all other measured targets unchanged.
        self.gui.scales[self.elbow].set(20)
        self.assertTrue(self.gui.holding)
        degrees[2] = 20
        for name, angle in zip(self.names, degrees):
            self.assertAlmostEqual(self.gui.target_deg[name], angle)
        self.assertAlmostEqual(self.gui.target_aperture_mm, 35)

    def test_gripper_drag_reholds_without_changing_arm(self):
        self.gui.toggle_hold()
        self.gui.actual_deg = dict.fromkeys(self.names, 15)
        self.gui.actual_aperture_mm = 24
        self.poll()
        self.gui.aperture_scale.set(50)
        self.assertTrue(self.gui.holding)
        self.assertEqual(self.gui.target_deg, dict.fromkeys(self.names, 15))
        self.worker_once()
        self.assertEqual(self.setcfg.call_args.kwargs["joint_positions"],
                         [math.radians(15)] * 4 + [0.025, 0.025])

    def test_hold_button_uses_tracked_targets(self):
        self.gui.toggle_hold()
        self.gui.actual_deg = dict.fromkeys(self.names, -30)
        self.gui.actual_aperture_mm = 42
        self.poll()
        self.gui.toggle_hold()
        self.worker_once()
        self.assertTrue(self.gui.holding)
        self.assertEqual(self.gui.hold_btn["text"], "Release")
        self.assertEqual(self.setcfg.call_args.kwargs["joint_positions"],
                         [math.radians(-30)] * 4 + [0.021, 0.021])

    def test_holding_feedback_does_not_overwrite_targets(self):
        self.gui.scales["elbow_joint"].set(70)
        self.gui.aperture_scale.set(60)
        self.worker_once()
        self.poll()
        self.assertEqual(self.gui.target_deg["elbow_joint"], 70)
        self.assertEqual(self.gui.aperture_scale.get(), 60)
        self.assertEqual(self.gui.target_aperture_mm, 60)
        self.assertEqual(self.gui.actual_aperture_mm, 0)

    def test_continuous_feedback_wraps_but_aperture_is_not_an_angle(self):
        self.gui.toggle_hold()
        self.getj.side_effect = lambda name: SimpleNamespace(
            success=True, position=[0.04 if name.split("::")[-1] in FINGER_NAMES else 5 * math.pi / 2])
        self.worker_once()
        self.poll()
        self.assertEqual(self.gui.target_deg, dict.fromkeys(self.names, 90))
        self.assertEqual(self.gui.actual_aperture_mm, 80)
        self.assertEqual(self.gui.target_aperture_mm, 80)
        self.assertFalse(self.gui.holding)

    def test_out_of_range_feedback_is_displayed_but_target_stays_safe(self):
        self.gui.toggle_hold()
        for actual, target in [(-1, 0), (82, 80)]:
            self.gui.actual_aperture_mm = actual
            self.poll()
            self.assertEqual(self.gui.actual_aperture_mm, actual)
            self.assertEqual(self.gui.target_aperture_mm, target)
            self.assertEqual(self.gui.aperture_scale.get(), target)
            self.assertFalse(self.gui.holding)

    def test_gui_joints_match_expanded_rig_independent_of_xml_order(self):
        env = dict(os.environ, PATH="/opt/ros/noetic/bin:/usr/bin:/bin", PYTHONNOUSERSITE="1",
                   PYTHONPATH="/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages")
        rig = Path(__file__).resolve().parents[1] / "urdf" / "rig.urdf.xacro"
        xml = subprocess.check_output(["/opt/ros/noetic/bin/xacro", str(rig)], env=env, timeout=15)
        all_joints = ElementTree.fromstring(xml).findall("joint")
        self.assertTrue(REMOVED_NAMES.isdisjoint(joint.attrib["name"] for joint in all_joints))
        joints = {joint.attrib["name"]: joint for joint in all_joints
                  if joint.attrib["type"] != "fixed"}
        self.assertEqual(set(PHYSICAL_NAMES), set(joints))
        axes = [(0, 1, 0), (1, 0, 0), (0, 1, 0), (1, 0, 0)]
        for name, axis in zip(ARM_NAMES, axes):
            with self.subTest(joint=name):
                self.assertEqual(joints[name].attrib["type"], "continuous")
                self.assertEqual(tuple(map(float, joints[name].find("axis").attrib["xyz"].split())), axis)
                self.assertIsNone(joints[name].find("mimic"))
        finger_axes = []
        for name in FINGER_NAMES:
            joint = joints[name]
            self.assertEqual(joint.attrib["type"], "prismatic")
            self.assertIsNone(joint.find("mimic"))
            self.assertEqual(float(joint.find("limit").attrib["lower"]), 0)
            self.assertAlmostEqual(float(joint.find("limit").attrib["upper"]), 0.04)
            axis = tuple(map(float, joint.find("axis").attrib["xyz"].split()))
            self.assertIn(axis, [(0, 1, 0), (0, -1, 0)])
            finger_axes.append(axis)
        self.assertEqual(finger_axes[0], tuple(-value for value in finger_axes[1]))
        # Follow actual topology through fixed links, never XML element order.
        by_child = {joint.find("child").attrib["link"]: joint for joint in all_joints}
        gripper_mount = by_child["gripper_base"]
        self.assertEqual(gripper_mount.attrib["type"], "fixed")
        self.assertEqual(gripper_mount.find("parent").attrib["link"],
                 joints["wrist_roll_joint"].find("child").attrib["link"])
        for name in FINGER_NAMES:
            ancestors = []
            joint = joints[name]
            seen = set()
            while joint is not None:
                joint_name = joint.attrib["name"]
                self.assertNotIn(joint_name, seen, "Cyclic joint chain")
                seen.add(joint_name)
                if joint.attrib["type"] != "fixed":
                    ancestors.append(joint_name)
                joint = by_child.get(joint.find("parent").attrib["link"])
            self.assertEqual(list(reversed(ancestors)), ARM_NAMES + [name])

    def test_six_controls_in_two_columns_three_rows_and_status_fit_900px_screen(self):
        self.root.deiconify()
        self.root.update_idletasks()
        self.assertLessEqual(self.root.winfo_height(), 850)
        scales = [*self.gui.scales.values(), self.gui.aperture_scale]
        self.assertEqual(len(scales), 5)
        for index, scale in enumerate(scales):
            group = scale.master.master
            expected_grid = (index // 2, index % 2) if index < 4 else (2, 0)
            self.assertEqual((group.grid_info()["row"], group.grid_info()["column"]), expected_grid)
        self.assertEqual(scales[0].master.master.master.grid_size(), (2, 3))
        for widget in [*self.gui.scales.values(), *self.gui.value_labels.values(),
                       *self.gui.actual_labels.values(), self.gui.aperture_scale,
                       self.gui.aperture_target_label, self.gui.aperture_actual_label,
                       self.gui.hold_btn, self.gui.status]:
            bottom = widget.winfo_rooty() - self.root.winfo_rooty() + widget.winfo_height()
            right = widget.winfo_rootx() - self.root.winfo_rootx() + widget.winfo_width()
            self.assertTrue(widget.winfo_ismapped())
            self.assertLessEqual(bottom, self.root.winfo_height())
            self.assertLessEqual(right, self.root.winfo_width())

    def test_rejected_command_is_displayed(self):
        self.setcfg.return_value = SimpleNamespace(success=False, status_message="Missing elbow joint")
        self.worker_once()
        self.poll()
        self.assertEqual(self.gui.status["text"], "Missing elbow joint")

    def test_service_failures_are_visible_and_nonfatal(self):
        self.setcfg.side_effect = RuntimeError("service offline")
        self.getj.side_effect = RuntimeError("service offline")
        self.worker_once()
        self.poll()
        self.assertIn("service offline", self.gui.status["text"])
        self.assertTrue(all("no feedback" in label["text"]
                            for label in self.gui.actual_labels.values()))
        self.assertIn("no feedback", self.gui.aperture_actual_label["text"])

    def test_missing_finger_feedback_keeps_last_target_without_reholding(self):
        self.gui.aperture_scale.set(30)
        self.gui.toggle_hold()
        for bad_response in [SimpleNamespace(success=False, position=[], status_message="Missing finger"),
                             SimpleNamespace(success=True, position=[]),
                             SimpleNamespace(success=True, position=[float("nan")]),
                             SimpleNamespace(success=True, position=[float("inf")])]:
            with self.subTest(response=bad_response):
                self.getj.side_effect = lambda name: (
                    bad_response if name.endswith("gripper_right_joint")
                    else SimpleNamespace(success=True, position=[0.01]))
                self.worker_once()
                self.poll()
                self.assertIsNone(self.gui.actual_aperture_mm)
                self.assertEqual(self.gui.target_aperture_mm, 30)
                self.assertIn("no feedback", self.gui.aperture_actual_label["text"])
                self.assertIn("gripper_right_joint", self.gui.status["text"])
                self.assertFalse(self.gui.holding)
        self.setcfg.assert_not_called()

    def test_rejected_command_without_detail_has_useful_error(self):
        self.setcfg.return_value = SimpleNamespace(success=False, status_message="")
        self.worker_once()
        self.poll()
        self.assertIn("4 arm joints and 2 fingers", self.gui.status["text"])

    def test_worker_uses_no_tk_on_real_background_thread(self):
        errors = []

        def run():
            try:
                self.worker_once()
            except Exception as exc:
                errors.append(exc)

        with patch.object(tk.Variable, "get") as get_var, \
                patch.object(tk.Variable, "set") as set_var, \
                patch.object(tk.ttk.Widget, "config") as config, \
                patch.object(tk.ttk.Widget, "configure") as configure, \
                patch.object(self.root, "after") as after:
            worker = threading.Thread(target=run, daemon=True)
            worker.start()
            worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(errors, [])
            for method in (get_var, set_var, config, configure, after):
                method.assert_not_called()
        self.setcfg.assert_called_once()
        self.assertEqual(self.getj.call_count, 6)

    def test_ui_poll_does_not_call_ros(self):
        self.poll()
        self.setcfg.assert_not_called()
        self.getj.assert_not_called()

    def test_shutdown_cancels_poll_and_prevents_rescheduling(self):
        self.gui.shutdown()
        self.assertTrue(self.gui.stop_event.is_set())
        self.gui.thread.join.assert_called_with(timeout=1.0)
        with patch.object(self.root, "after") as after:
            self.gui._poll_actual()
            after.assert_not_called()


if __name__ == "__main__":
    unittest.main()