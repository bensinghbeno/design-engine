import unittest

from detect_gestures import GestureState, classify_pose, parse_roi


class GestureTests(unittest.TestCase):
    def pose(self):
        points = [[100.0, 100.0, 1.0] for _ in range(17)]
        for index, position in {5: (80, 100), 6: (120, 100), 9: (70, 180), 10: (130, 180),
                                11: (80, 200), 12: (120, 200), 13: (80, 270), 14: (120, 270),
                                15: (80, 350), 16: (120, 350)}.items():
            points[index][:2] = position
        return points

    def test_arm_labels_and_missing_wrist(self):
        points = self.pose()
        self.assertEqual(classify_pose(points)[0], set())
        points[9][1] = 50
        self.assertEqual(classify_pose(points)[0], {"Left Hand Up"})
        points[10][1] = 50
        self.assertEqual(classify_pose(points)[0], {"Both Hands Up"})
        points[9][2] = 0
        self.assertEqual(classify_pose(points)[0], {"Right Hand Up"})

    def test_leg_raise(self):
        points = self.pose()
        points[13][1] = 220
        points[15][1] = 260
        self.assertEqual(classify_pose(points)[0], {"Left Leg Up"})

    def test_stand_normal(self):
        from gesture_script import ScriptRunner, required_visible
        points = self.pose()
        for index, position in {0: (100, 60), 1: (92, 50), 2: (108, 50),
                                5: (70, 100), 6: (130, 100), 7: (70, 155), 8: (130, 155),
                                9: (70, 210), 10: (130, 210), 13: (85, 270), 14: (115, 270),
                                15: (90, 350), 16: (110, 350)}.items():
            points[index][:2] = position
        self.assertEqual(classify_pose(points)[0], {"Stand Normal"})
        runner = ScriptRunner([], speaker=lambda text: None)
        runner.expected = "Stand Normal"
        runner.phase = "Respond"
        self.assertIn("Matched", runner.assess(1, classify_pose(points)[0], points, .5)[0])
        self.assertEqual(runner.feedback_pending, ["success"])
        for index, position in ((9, (70, 50)), (7, (30, 155)), (13, (125, 230)),
                                (15, (20, 350)), (0, (145, 60)), (5, (70, 150))):
            altered = [point[:] for point in points]
            altered[index][:2] = position
            with self.subTest(index=index):
                self.assertNotIn("Stand Normal", classify_pose(altered)[0])
        for index in (0, 7, 9, 13, 15):
            hidden = [point[:] for point in points]
            hidden[index][2] = 0
            self.assertNotIn("Stand Normal", classify_pose(hidden)[0])
            self.assertFalse(required_visible("Stand Normal", hidden, .5))

    def test_missing_torso(self):
        points = self.pose()
        points[5][2] = 0
        self.assertEqual(classify_pose(points), (set(), "Unknown"))

    def test_hold_and_release(self):
        state = GestureState()
        self.assertEqual(state.update({"Both Hands Up"}, "Unknown", 0, .4, .15), set())
        self.assertEqual(state.update({"Both Hands Up"}, "Unknown", .5, .4, .15), {"Both Hands Up"})
        self.assertEqual(state.update(set(), "Unknown", .7, .4, .15), set())

    def test_no_turn_from_missing_face(self):
        state = GestureState()
        for timestamp in (0, .5, 1):
            self.assertEqual(state.update(set(), "Unknown", timestamp, .4, .15, True), set())

    def test_polygon(self):
        self.assertEqual(parse_roi("0,0;100,0;100,100"), [(0, 0), (100, 0), (100, 100)])


class RecordingTests(unittest.TestCase):
    def test_live_recording_timestamps(self):
        import tempfile
        from pathlib import Path
        import av
        import numpy as np
        from live_capture import LiveVideoWriter
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.mp4"
            writer = LiveVideoWriter(path, 320, 240, 30)
            try:
                for timestamp in (10.0, 10.1, 10.5):
                    writer.write(np.zeros((240, 320, 3), dtype=np.uint8), timestamp)
            finally:
                writer.release()
            with av.open(str(path)) as container:
                times = [float(frame.pts * frame.time_base) for frame in container.decode(video=0)]
            self.assertEqual(len(times), 3)
            self.assertAlmostEqual(times[0], 0, places=2)
            self.assertAlmostEqual(times[-1], .5, places=2)


class RunLogTests(unittest.TestCase):
    def test_traceback_and_overwrite(self):
        import tempfile
        from pathlib import Path
        from run_log import run_logged
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.log"

            def failure():
                print("Before failure")
                raise RuntimeError("Intentional test failure")

            self.assertEqual(run_logged(failure, path), 1)
            content = path.read_text()
            self.assertIn("Before failure", content)
            self.assertIn("Traceback", content)
            self.assertIn("Intentional test failure", content)
            self.assertEqual(run_logged(lambda: print("Fresh run"), path), 0)
            self.assertIn("Fresh run", path.read_text())
            self.assertNotIn("Intentional test failure", path.read_text())


class SpeechTests(unittest.TestCase):
    def test_feedback_once_per_outcome(self):
        from gesture_script import ScriptRunner
        runner = ScriptRunner([], speaker=lambda text: None)
        runner.expected = "Left Hand Up"
        runner.phase = "Respond"
        points = [[0, 0, 1] for _ in range(17)]
        for _ in range(10):
            runner.assess(1, {"Right Hand Up"}, points, .5)
        for _ in range(10):
            runner.assess(1, {"Left Hand Up"}, points, .5)
        self.assertEqual(runner.feedback_pending, ["wrong", "success"])
        played = []
        runner.play_feedback = played.append
        runner.drain_feedback()
        self.assertEqual(played, ["wrong", "success"])
        self.assertEqual(runner.feedback_pending, [])

    def test_feedback_deadline_and_unknown(self):
        from gesture_script import ScriptRunner, parse_script
        for visible, expected in ((True, ["wrong"]), (False, [])):
            runner = ScriptRunner(parse_script("Left Hand Up\n[delay 3 sec]"), speaker=lambda text: None)
            played = []
            runner.play_feedback = played.append

            def wait(seconds):
                if seconds == 3:
                    runner.assess(1, set(), [[0, 0, int(visible)] for _ in range(17)], .5)
                runner.drain_feedback()

            runner.wait = wait
            runner.thread.start()
            runner.thread.join(timeout=2)
            self.assertFalse(runner.thread.is_alive())
            self.assertIsNone(runner.error)
            self.assertEqual(played, expected)

    def test_wrong_tone_precedes_warning(self):
        from gesture_script import ScriptRunner
        events = []
        runner = ScriptRunner([], speaker=lambda text: events.append(text))
        runner.run_audio_command = lambda command: events.append("tone")
        runner.play_feedback("wrong")
        self.assertEqual(events, ["tone", "Wrong gesture detected"])

    def test_only_plain_text_reaches_speaker(self):
        from gesture_script import ScriptRunner, parse_script
        spoken = []
        runner = ScriptRunner(parse_script("Hello [delay 0 sec]\nLeft Hand Up\n[visual cue]\nThanks"), speaker=spoken.append)
        runner.thread.start()
        runner.thread.join(timeout=2)
        self.assertFalse(runner.thread.is_alive())
        self.assertIsNone(runner.error)
        self.assertEqual(spoken, ["Hello", "Left Hand Up", "Thanks"])

    def test_invalid_brackets_rejected(self):
        from gesture_script import parse_script
        for text in ("Hello [oops", "Hello [nested [cue]]", "[delay invalid sec]"):
            with self.assertRaises(ValueError):
                parse_script(text)


class PlaybackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playback import create_player
        cls.player = create_player(30, 301)

    @classmethod
    def tearDownClass(cls):
        cls.player.close()

    def test_click_and_drag_seek(self):
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtTest import QTest

        player = self.player
        player.app.processEvents()
        slider = player.timeline
        for fraction, expected in ((0.75, 225), (0.25, 75), (0, 0), (1, 300)):
            position = QPoint(round((slider.width() - 1) * fraction), slider.height() // 2)
            QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=position)
            self.assertLessEqual(abs(player.pending_seek - expected), 3)
        QTest.mousePress(slider, Qt.MouseButton.LeftButton, pos=QPoint(10, slider.height() // 2))
        QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, pos=QPoint(slider.width() // 2, slider.height() // 2))
        self.assertLessEqual(abs(player.pending_seek - 150), 2)
        self.assertFalse(slider.isSliderDown())
        player.pending_seek = None

    def test_arrow_seeking(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest

        player = self.player
        player.current_frame = 150
        for widget in (player, player.timeline, player.play):
            QTest.keyClick(widget, Qt.Key.Key_Left)
            self.assertEqual(player.pending_seek, 60)
            QTest.keyClick(widget, Qt.Key.Key_Right)
            self.assertEqual(player.pending_seek, 240)
        player.pending_seek = None
        player.fps_field.setText("30")
        player.fps_field.setCursorPosition(2)
        QTest.keyClick(player.fps_field, Qt.Key.Key_Left)
        self.assertEqual(player.fps_field.cursorPosition(), 1)
        self.assertIsNone(player.pending_seek)

    def test_controls(self):
        player = self.player
        player.play.click()
        self.assertTrue(player.paused)
        player.fps_field.setText("12")
        player.apply.click()
        self.assertEqual(player.playback_fps, 12)
        for value in ("nan", "0", "-1", "abc", "241"):
            player.fps_field.setText(value)
            player.apply.click()
            self.assertEqual(player.playback_fps, 12)
            self.assertTrue(player.error.text())
        player.current_frame = 150
        player.previous.click()
        self.assertEqual(player.next_action(), 60)
        player.following.click()
        self.assertEqual(player.next_action(), 240)
        player.timeline.setValue(299)
        self.assertEqual(player.next_action(), 299)
        self.assertTrue(player.paused)
        player.request_seek(-90)
        self.assertEqual(player.next_action(), 0)
        player.request_seek(999)
        self.assertEqual(player.next_action(), 300)
        player.ended = True
        player.play.click()
        self.assertFalse(player.paused)
        self.assertEqual(player.next_action(), 0)


if __name__ == "__main__":
    unittest.main()