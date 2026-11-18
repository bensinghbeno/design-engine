import argparse
import math
from pathlib import Path
import struct
import tempfile
import time
import unittest
from unittest.mock import Mock, call, patch

from control import LOGGER, Link, bounded, configure_logging, detect, main, packet, rotate, timed_torque


class ControlTests(unittest.TestCase):
    def test_relative_angle_crossing_both_directions_and_wrap(self):
        for direction in (1, -1):
            origin = direction * (4 * math.pi - 0.05)
            end = origin + direction * math.radians(11)
            end = (end + 4 * math.pi) % (8 * math.pi) - 4 * math.pi
            link = Mock(last_feedback=(origin, 0.0, 25.0))
            def feedback():
                if link.feedback.call_count == 1:
                    return 0
                if link.feedback.call_count > 2:
                    link.last_feedback = (end, 0.2, 25.0)
                return 2
            link.feedback.side_effect = feedback
            with patch("control.detect", return_value=48), patch("control.time.sleep"):
                timed_torque(link, direction * 0.2, 1, angle_deg=direction * 10)
            self.assertEqual(link.command_torque.call_args_list, [call(0), call(direction * 0.2)])
            self.assertEqual(link.mock_calls[-1], call.stop())

    def test_angle_timeout_disables(self):
        link = Mock(last_feedback=(0.0, 0.0, 25.0))
        link.feedback.side_effect = [0, 2]
        with patch("control.detect", return_value=48), patch(
            "control.time.monotonic", side_effect=[0, 2]
        ), self.assertRaisesRegex(TimeoutError, "Angle target"):
            timed_torque(link, 0.2, 1, angle_deg=10)
        self.assertEqual(link.mock_calls[-1], call.stop())

    def test_invalid_angle_never_touches_motor(self):
        for angle in (0, -10, 30, float("nan"), float("inf")):
            link = Mock()
            with self.assertRaises(ValueError):
                timed_torque(link, 0.2, 1, angle_deg=angle)
            self.assertEqual(link.mock_calls, [])

    def test_torque_frame(self):
        port = Mock()
        link = Link(port, 127, 253)
        for torque_nm in (-8, 0, 0.2, 8):
            link.command_torque(torque_nm)
            frame = port.write.call_args.args[0]
            can_id = int.from_bytes(frame[2:6], "big") >> 3
            self.assertEqual(can_id >> 24, 1)
            self.assertEqual(can_id & 255, 127)
            decoded = ((can_id >> 8) & 65535) / 65535 * 28 - 14
            self.assertAlmostEqual(decoded, torque_nm, delta=28 / 65535)
            self.assertEqual(frame[7:15], bytes.fromhex("7fff7fff00000000"))
        link.command_torque(0.2)
        self.assertEqual(port.write.call_args.args[0].hex(), "41540c0e9bfc087fff7fff000000000d0a")

    def test_timed_torque_stops_at_deadline(self):
        link = Mock(last_feedback=(0.0, 0.0, 25.0))
        link.feedback.side_effect = [0, 2, 2]
        with patch("control.detect", return_value=48), patch("control.time.sleep"), patch(
            "control.time.monotonic", side_effect=[0, 0, 1]
        ):
            timed_torque(link, 0.2, 0.1)
        self.assertEqual(link.command_torque.call_args_list, [call(0), call(0.2)])
        self.assertLess(link.mock_calls.index(call.checked_write(0x7028, 10000, "I")),
                        link.mock_calls.index(call.send(3)))
        self.assertEqual(link.mock_calls[-1], call.stop())

    def test_torque_trips_and_feedback_failure_stop(self):
        for sample in ((0, 1.1, 25), (0.4, 0, 25), (0, 0, 60), (0, float("nan"), 25)):
            link = Mock(last_feedback=(0.0, 0.0, 25.0))
            def feedback():
                if link.feedback.call_count == 1:
                    return 0
                link.last_feedback = sample
                return 2
            link.feedback.side_effect = feedback
            with patch("control.detect", return_value=48), self.assertRaises(RuntimeError):
                timed_torque(link, 8, 0.1)
            link.command_torque.assert_called_once_with(0)
            self.assertEqual(link.mock_calls[-1], call.stop())
        for error in (TimeoutError("lost"), KeyboardInterrupt()):
            link = Mock(last_feedback=(0.0, 0.0, 25.0))
            link.feedback.side_effect = [0, 2, error]
            with patch("control.detect", return_value=48), patch("control.time.sleep"), self.assertRaises(type(error)):
                timed_torque(link, 0.2, 0.1)
            self.assertEqual(link.mock_calls[-1], call.stop())

    def test_torque_setup_failure_never_enables(self):
        link = Mock()
        link.checked_write.side_effect = RuntimeError("rejected")
        with patch("control.detect", return_value=48), self.assertRaises(RuntimeError):
            timed_torque(link, 0.2, 0.1)
        link.send.assert_not_called()
        self.assertEqual(link.stop.call_count, 2)

    def test_log_files_and_feedback(self):
        with tempfile.TemporaryDirectory() as directory:
            try:
                with patch("control.__file__", str(Path(directory) / "control.py")):
                    configure_logging(argparse.Namespace(command="rotate", current=1.2))
                link = Link(Mock(), 127, 253)
                link.receive = Mock(return_value=(2, (2 << 24) | (2 << 22) | (127 << 8) | 253,
                                                   struct.pack(">HHHH", 32768, 32768, 32768, 250)))
                self.assertEqual(link.feedback(), 2)
                LOGGER.error("test failure")
                logs = list((Path(directory) / "logs").glob("*.log"))
                self.assertEqual(len(logs), 2)
                for path in logs:
                    text = path.read_text()
                    self.assertIn("'current': 1.2", text)
                    self.assertIn("estimated_torque_Nm=", text)
                    self.assertIn("temperature_C=25.0", text)
                    self.assertIn("test failure", text)
            finally:
                for handler in LOGGER.handlers[:]:
                    handler.close()
                    LOGGER.removeHandler(handler)

    def test_packet(self):
        self.assertEqual(packet(17, 1, 253, bytes(8)),
                         b"AT" + bytes.fromhex("8807e80c") + b"\x08" + bytes(8) + b"\r\n")

    def test_fragmented_reply_with_noise(self):
        reply = packet(17, 253, 1, struct.pack("<H", 0x701C) + bytes(2) + struct.pack("<f", 48))
        port = Mock(in_waiting=0)
        port.read.side_effect = [b"noise"] + [bytes([byte]) for byte in reply]
        self.assertEqual(Link(port, 1, 253).read(0x701C), 48)
        self.assertEqual(port.write.call_args.args[0][2] >> 3, 17)

    def test_timeout(self):
        port = Mock(in_waiting=0)
        port.read.return_value = b""
        with self.assertRaises(TimeoutError):
            Link(port, 1, 253).receive(time.monotonic() - 1)

    def test_detect_only_reads(self):
        link = Mock()
        link.read.side_effect = [2, 48.0, 0.0, 0.0]
        detect(link)
        link.send.assert_not_called()
        link.write.assert_not_called()
        link.stop.assert_not_called()

    def test_configuration_failure_never_enables_and_stops(self):
        link = Mock()
        link.checked_write.side_effect = RuntimeError("unsupported watchdog")
        with patch("control.detect", return_value=48), self.assertRaises(RuntimeError):
            rotate(link, 0.2, 2, 0.5, 0.5)
        link.send.assert_not_called()
        self.assertEqual(link.stop.call_count, 2)

    def test_feedback_loss_stops(self):
        link = Mock()
        link.feedback.side_effect = [2, TimeoutError("lost")]
        with patch("control.detect", return_value=48), self.assertRaises(TimeoutError):
            rotate(link, 0.2, 2, 0.5, 0.5)
        link.send.assert_called_once_with(3)
        self.assertEqual(link.stop.call_count, 2)

    def test_invalid_speed(self):
        for value in ["nan", "inf", "1.01", "-1.01"]:
            with self.assertRaises(argparse.ArgumentTypeError):
                bounded(value, -1.0, 1.0)

    def test_cli_current_limits_without_hardware(self):
        for current, confirmation, accepted in (
            ("8.0", "--confirm-secured-load-rs00", True),
            ("8.01", "--confirm-secured-load-rs00", False),
            ("8.0", "--confirm-unloaded-rs00", False),
        ):
            arguments = ["control.py", "rotate", "--port", "/dev/ttyUSB0",
                         "--motor-id", "127", "--speed", "1.0", "--current", current,
                         "--acceleration", "0.5", "--seconds", "5", confirmation]
            with patch("sys.argv", arguments), patch("sys.stderr"), patch(
                "control.configure_logging", side_effect=RuntimeError("parsed without hardware")
            ) as logging_setup:
                if accepted:
                    with self.assertRaisesRegex(RuntimeError, "parsed without hardware"):
                        main()
                    self.assertEqual(logging_setup.call_args.args[0].current, 8.0)
                else:
                    with self.assertRaises(SystemExit) as result:
                        main()
                    self.assertEqual(result.exception.code, 2)
                    logging_setup.assert_not_called()

    def test_cli_speed_limits_without_hardware(self):
        for speed in ("1.0", "-1.0", "1.01", "-1.01"):
            arguments = ["control.py", "rotate", "--port", "/dev/ttyUSB0",
                         "--motor-id", "127", "--speed", speed, "--current", "4.0",
                         "--acceleration", "0.5", "--seconds", "5",
                         "--confirm-secured-load-rs00"]
            with patch("sys.argv", arguments), patch("sys.stderr"), patch(
                "control.configure_logging", side_effect=RuntimeError("parsed without hardware")
            ) as logging_setup:
                if abs(float(speed)) <= 1:
                    with self.assertRaisesRegex(RuntimeError, "parsed without hardware"):
                        main()
                    self.assertEqual(logging_setup.call_args.args[0].speed, float(speed))
                else:
                    with self.assertRaises(SystemExit) as result:
                        main()
                    self.assertEqual(result.exception.code, 2)
                    logging_setup.assert_not_called()

    def test_each_run_configures_target_before_enable(self):
        link = Mock()
        link.feedback.return_value = 2
        link.read.return_value = 0.0
        for speed in (0.1, -0.1):
            link.reset_mock()
            with patch("control.detect", return_value=48), patch(
                "control.time.monotonic", side_effect=[0, 3, 3, 3]
            ):
                rotate(link, speed, 2, 0.5, 0.5)
            self.assertEqual(link.mock_calls[:8], [
                call.stop(),
                call.checked_write(0x7005, 2, "B"),
                call.checked_write(0x700A, 0.0),
                call.checked_write(0x7018, 0.5),
                call.checked_write(0x7022, 0.5),
                call.checked_write(0x7028, 10000, "I"),
                call.checked_write(0x700A, speed),
                call.send(3),
            ])
            self.assertEqual(link.mock_calls[-1], call.stop())

    def test_target_readback_failure_never_enables(self):
        link = Mock()
        link.checked_write.side_effect = [None] * 5 + [RuntimeError("target rejected")]
        with patch("control.detect", return_value=48), self.assertRaises(RuntimeError):
            rotate(link, 0.1, 2, 0.5, 0.5)
        link.send.assert_not_called()
        self.assertEqual(link.stop.call_count, 2)

    def test_success_sets_watchdog_before_enable(self):
        link = Mock()
        link.feedback.return_value = 2
        link.read.return_value = 0.0
        with patch("control.detect", return_value=48), patch("control.time.monotonic", side_effect=[0, 3, 3, 3]):
            rotate(link, 0.2, 2, 0.5, 0.5)
        calls = link.mock_calls
        from unittest.mock import call
        self.assertLess(calls.index(call.checked_write(0x7028, 10000, "I")),
                        calls.index(call.send(3)))
        link.write.assert_called_with(0x700A, 0.0)
        self.assertEqual(link.stop.call_count, 2)


if __name__ == "__main__":
    unittest.main()