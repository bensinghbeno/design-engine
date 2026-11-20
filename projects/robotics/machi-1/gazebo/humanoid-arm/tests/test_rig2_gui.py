import importlib.util
import math
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("rig2_gui", Path(__file__).resolve().parents[1] / "rig2/arm_gui.py")
rig2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rig2)


class Rig2GuiTests(unittest.TestCase):
    def test_widget_setup_has_four_limited_sliders_and_starts_released(self):
        root = rig2.tk.Tk()
        root.withdraw()
        try:
            with patch.object(rig2.threading, "Thread"):
                gui = rig2.Rig2Gui(root, Mock(), Mock(), Mock(return_value=False))
            root.update_idletasks()
            self.assertEqual(len(gui.scales), 4)
            self.assertFalse(gui.holding)
            for name, scale in gui.scales.items():
                self.assertEqual((float(scale["from"]), float(scale["to"])), gui.limits[name])
                self.assertTrue(scale.instate(["disabled"]))
            gui.shutdown()
        finally:
            root.destroy()

    def setUp(self):
        self.gui = rig2.Rig2Gui.__new__(rig2.Rig2Gui)
        self.gui.lock = threading.Lock()
        self.gui.limits = rig2.joint_limits()
        self.gui.holding = False
        self.gui.target = {name: 0.0 for name, _ in rig2.JOINTS}
        self.gui.actual = {name: None for name, _ in rig2.JOINTS}
        self.gui.error = "Waiting"
        self.gui.set_configuration = Mock(return_value=SimpleNamespace(success=True))
        self.gui.get_joint = Mock(return_value=SimpleNamespace(success=True, position=[0.1]))

    def test_limits_match_four_joint_rig(self):
        self.assertEqual(len(self.gui.limits), 4)
        self.assertEqual(self.gui.limits["shoulder_joint"], (-180, 180))
        for name in ("elbow_joint", "shoulder_roll_joint", "wrist_roll_joint"):
            self.assertEqual(self.gui.limits[name], (-135, 135))

    def test_released_feedback_never_commands_and_uses_only_rig2(self):
        self.gui.cycle()
        self.gui.set_configuration.assert_not_called()
        self.assertTrue(self.gui.ready())
        for name, _ in rig2.JOINTS:
            self.gui.get_joint.assert_any_call(f"rig2_servo_arm::{name}")
            self.assertAlmostEqual(self.gui.target[name], math.degrees(0.1))

    def test_hold_commands_four_joints_and_clamps(self):
        self.gui.cycle()
        self.gui.slide("elbow_joint", "180")
        self.gui.cycle()
        args = self.gui.set_configuration.call_args.kwargs
        self.assertEqual(args["model_name"], "rig2_servo_arm")
        self.assertEqual(args["joint_names"], [name for name, _ in rig2.JOINTS])
        self.assertEqual(len(args["joint_positions"]), 4)
        self.assertAlmostEqual(args["joint_positions"][2], math.radians(135))

    def test_missing_feedback_blocks_hold_and_reset(self):
        self.gui.toggle_hold()
        self.gui.reset()
        self.gui.slide("elbow_joint", "45")
        self.assertFalse(self.gui.holding)
        self.gui.get_joint.side_effect = RuntimeError("no model")
        self.gui.cycle()
        self.assertFalse(self.gui.ready())
        self.assertEqual(self.gui.error, "no model")

    def test_failure_releases_hold(self):
        self.gui.cycle()
        self.gui.toggle_hold()
        self.gui.set_configuration.return_value = SimpleNamespace(success=False, status_message="rejected")
        self.gui.cycle()
        self.assertFalse(self.gui.holding)
        self.assertEqual(self.gui.error, "rejected")

    def test_reset_and_release(self):
        self.gui.cycle()
        self.gui.reset()
        self.assertTrue(self.gui.holding)
        self.assertEqual(set(self.gui.target.values()), {0.0})
        self.gui.toggle_hold()
        self.assertFalse(self.gui.holding)


if __name__ == "__main__":
    unittest.main()