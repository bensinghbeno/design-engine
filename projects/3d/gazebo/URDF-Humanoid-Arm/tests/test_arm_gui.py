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
        self.yaw, self.pitch = self.names

    def tearDown(self):
        self.gui.shutdown()
        self.root.destroy()

    def poll(self):
        self.root.after_cancel(self.gui.poll_id)
        self.gui._poll_actual()

    def worker_once(self):
        self.gui.stop_event.clear()
        with patch.object(self.gui.stop_event, "wait", side_effect=lambda _: self.gui.stop_event.set()):
            self.gui._hold_loop()

    def test_sliders_start_centered_and_independent(self):
        for name in self.names:
            scale = self.gui.scales[name]
            self.assertEqual(float(scale["from"]), -180)
            self.assertEqual(float(scale["to"]), 180)
            self.assertEqual(scale.get(), 0)
        self.gui.scales[self.yaw].set(90)
        self.gui.scales[self.pitch].set(-45)
        self.assertEqual(self.gui.target_deg, {self.yaw: 90, self.pitch: -45})

    def test_worker_commands_pair_in_radians_and_reads_scoped_names(self):
        self.gui.scales[self.yaw].set(90)
        self.gui.scales[self.pitch].set(-45)
        self.worker_once()
        self.setcfg.assert_called_once_with(
            model_name="arm_rig", urdf_param_name="robot_description",
            joint_names=self.names, joint_positions=[math.pi / 2, -math.pi / 4])
        self.assertEqual([call.args[0] for call in self.getj.call_args_list],
                         ["arm_rig::" + name for name in self.names])

    def test_reset_both_and_reengage_hold(self):
        self.gui.scales[self.yaw].set(65)
        self.gui.scales[self.pitch].set(-35)
        self.gui.toggle_hold()
        self.gui.reset()
        self.assertTrue(self.gui.holding)
        self.assertEqual(self.gui.target_deg, dict.fromkeys(self.names, 0))
        self.assertTrue(all(scale.get() == 0 for scale in self.gui.scales.values()))

    def test_release_tracks_both_without_reholding(self):
        self.gui.toggle_hold()
        self.getj.side_effect = [SimpleNamespace(success=True, position=[math.pi / 3]),
                                 SimpleNamespace(success=True, position=[-math.pi / 2])]
        self.worker_once()
        self.setcfg.assert_not_called()
        self.poll()
        self.assertFalse(self.gui.holding)
        self.assertAlmostEqual(self.gui.scales[self.yaw].get(), 60)
        self.assertAlmostEqual(self.gui.scales[self.pitch].get(), -90)
        self.assertEqual(self.gui.hold_btn["text"], "Hold")
        # Dragging yaw re-holds with the last measured pitch unchanged.
        self.gui.scales[self.yaw].set(20)
        self.assertTrue(self.gui.holding)
        self.assertAlmostEqual(self.gui.target_deg[self.pitch], -90)

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