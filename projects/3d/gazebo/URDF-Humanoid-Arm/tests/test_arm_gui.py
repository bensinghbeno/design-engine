"""Real Tk widgets with mocked Gazebo services; run under a display or Xvfb."""
import importlib.util
import math
from pathlib import Path
import sys
import tkinter as tk
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


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
        self.pitch, self.roll, self.yaw = self.names

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
        self.assertEqual(self.names, ["shoulder_joint", "shoulder_roll_joint", "shoulder_yaw_joint"])
        for name in self.names:
            scale = self.gui.scales[name]
            self.assertEqual(float(scale["from"]), -180)
            self.assertEqual(float(scale["to"]), 180)
            self.assertEqual(scale.get(), 0)
        self.gui.scales[self.yaw].set(90)
        self.gui.scales[self.pitch].set(-45)
        self.assertEqual(self.gui.target_deg, {self.yaw: 90, self.pitch: -45, self.roll: 0})
        self.gui.scales[self.roll].set(30)
        self.assertEqual(self.gui.target_deg, {self.yaw: 90, self.pitch: -45, self.roll: 30})

    def test_worker_commands_all_three_in_radians_and_reads_scoped_names(self):
        self.gui.scales[self.yaw].set(90)
        self.gui.scales[self.pitch].set(-45)
        self.gui.scales[self.roll].set(30)
        self.worker_once()
        self.setcfg.assert_called_once_with(
            model_name="arm_rig", urdf_param_name="robot_description",
            joint_names=self.names, joint_positions=[-math.pi / 4, math.pi / 6, math.pi / 2])
        self.assertEqual([call.args[0] for call in self.getj.call_args_list],
                         ["arm_rig::" + name for name in self.names])

    def test_reset_all_and_reengage_hold(self):
        self.gui.scales[self.yaw].set(65)
        self.gui.scales[self.pitch].set(-35)
        self.gui.scales[self.roll].set(20)
        self.gui.toggle_hold()
        self.gui.reset()
        self.assertTrue(self.gui.holding)
        self.assertEqual(self.gui.target_deg, dict.fromkeys(self.names, 0))
        self.assertTrue(all(scale.get() == 0 for scale in self.gui.scales.values()))

    def test_release_tracks_all_without_reholding(self):
        self.gui.toggle_hold()
        self.getj.side_effect = [SimpleNamespace(success=True, position=[-math.pi / 2]),
                                 SimpleNamespace(success=True, position=[math.pi / 4]),
                                 SimpleNamespace(success=True, position=[math.pi / 3])]
        self.worker_once()
        self.setcfg.assert_not_called()
        self.poll()
        self.assertFalse(self.gui.holding)
        self.assertAlmostEqual(self.gui.scales[self.yaw].get(), 60)
        self.assertAlmostEqual(self.gui.scales[self.pitch].get(), -90)
        self.assertAlmostEqual(self.gui.scales[self.roll].get(), 45)
        self.assertEqual(self.gui.hold_btn["text"], "Hold")
        # Dragging yaw re-holds with the measured pitch and roll unchanged.
        self.gui.scales[self.yaw].set(20)
        self.assertTrue(self.gui.holding)
        self.assertAlmostEqual(self.gui.target_deg[self.pitch], -90)
        self.assertAlmostEqual(self.gui.target_deg[self.roll], 45)

    def test_gui_joint_order_matches_expanded_rig(self):
        import os
        import subprocess
        from xml.etree import ElementTree

        env = dict(os.environ, PATH="/opt/ros/noetic/bin:/usr/bin:/bin", PYTHONNOUSERSITE="1",
                   PYTHONPATH="/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages")
        rig = Path(__file__).resolve().parents[1] / "urdf" / "rig.urdf.xacro"
        xml = subprocess.check_output(["/opt/ros/noetic/bin/xacro", str(rig)], env=env, timeout=15)
        joints = [joint.attrib["name"] for joint in ElementTree.fromstring(xml).findall("joint")
                  if joint.attrib["type"] != "fixed"]
        self.assertEqual(self.names, joints)

    def test_three_controls_and_status_fit_window(self):
        self.root.deiconify()
        self.root.update_idletasks()
        for widget in [*self.gui.scales.values(), self.gui.hold_btn, self.gui.status]:
            bottom = widget.winfo_rooty() - self.root.winfo_rooty() + widget.winfo_height()
            self.assertTrue(widget.winfo_ismapped())
            self.assertLessEqual(bottom, self.root.winfo_height())

    def test_rejected_command_is_displayed(self):
        self.setcfg.return_value = SimpleNamespace(success=False, status_message="Missing yaw joint")
        self.worker_once()
        self.poll()
        self.assertEqual(self.gui.status["text"], "Missing yaw joint")

    def test_service_failures_are_visible_and_nonfatal(self):
        self.setcfg.side_effect = RuntimeError("service offline")
        self.getj.side_effect = RuntimeError("service offline")
        self.worker_once()
        self.poll()
        self.assertIn("service offline", self.gui.status["text"])
        self.assertTrue(all("no feedback" in label["text"]
                            for label in self.gui.actual_labels.values()))

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