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

    def test_foot_lift_without_high_knee(self):
        points = self.pose()
        points[13][1] = 265
        points[15][1] = 315
        self.assertIn("Left Leg Up", classify_pose(points)[0])
        points[15][1] = 340
        self.assertNotIn("Left Leg Up", classify_pose(points)[0])
        points[15][1] = 315
        points[15][2] = 0
        self.assertNotIn("Left Leg Up", classify_pose(points)[0])

    def test_forward_bend_without_sideways_lean(self):
        points = self.pose()
        points[5][:2] = (70, 170)
        points[6][:2] = (130, 170)
        self.assertIn("Bend Down", classify_pose(points)[0])
        points[13][2] = 0
        self.assertNotIn("Bend Down", classify_pose(points)[0])
        points[13][2] = 1
        points[13][1] = points[14][1] = 210
        self.assertNotIn("Bend Down", classify_pose(points)[0])

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
    def test_audio_journal_and_interrupt_protection(self):
        import json
        import os
        import signal
        import tempfile
        from pathlib import Path
        from session_audio import SessionAudio
        with tempfile.TemporaryDirectory() as directory:
            audio = SessionAudio(Path(directory) / "session.mp4")
            audio.started = 10
            audio.record(["ffplay", "clip.mp3"], 11, 12)
            self.assertEqual(json.loads(audio.journal.read_text())[0][:2], [1, 1])
            previous = signal.getsignal(signal.SIGINT)

            def merge(video):
                os.kill(os.getpid(), signal.SIGINT)
                return True

            audio._merge = merge
            self.assertTrue(audio.merge("unused.mp4"))
            self.assertEqual(signal.getsignal(signal.SIGINT), previous)

    def test_audio_timeline_mux(self):
        import tempfile
        from pathlib import Path
        import av
        import numpy as np
        from live_capture import LiveVideoWriter
        from session_audio import SessionAudio
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.mp4"
            writer = LiveVideoWriter(path, 320, 240, 10)
            for index in range(20):
                writer.write(np.zeros((240, 320, 3), dtype=np.uint8), index / 10)
            writer.release()
            audio = SessionAudio()
            audio.started = 100
            audio.record(["ffplay", "-f", "lavfi", "sine=frequency=880:duration=0.3"], 100.5, 100.8)
            self.assertTrue(audio.merge(path))
            with av.open(str(path)) as container:
                self.assertEqual(len(container.streams.video), 1)
                self.assertEqual(container.streams.audio[0].codec_context.name, "aac")
                samples = np.concatenate([frame.to_ndarray().ravel() for frame in container.decode(audio=0)])
                self.assertLess(float(np.max(np.abs(samples[:8000]))), .001)
                self.assertGreater(float(np.max(np.abs(samples))), .01)

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
    def test_reference_image_during_readout_and_response(self):
        from gesture_script import ScriptRunner, parse_script
        observed = []
        runner = ScriptRunner(parse_script("[Read: Machee Says] Left Hand Up\n[delay 3 sec]\nThanks"),
                              speaker=lambda text: None)
        runner.speaker = lambda text: observed.append((text, runner.gesture_image()))
        runner.wait = lambda seconds: observed.append((runner.phase, runner.gesture_image()))
        runner.run()
        self.assertIsNone(runner.error)
        self.assertEqual(observed, [("Machee Says", "Left Hand Up"), ("Left Hand Up", "Left Hand Up"),
                                    ("Get ready", "Left Hand Up"), ("Respond", "Left Hand Up"),
                                    ("Result", "Left Hand Up"), ("Thanks", None)])
        self.assertIsNone(runner.gesture_image())

    def test_gtts_caches_audio_and_uses_recordable_playback(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from gesture_script import ScriptRunner
        commands = []
        runner = ScriptRunner([], speaker=lambda text: None)

        def audio_command(command):
            commands.append(command)
            if command[1] == "-c":
                self.assertIn("from gtts import gTTS", command[2])
                self.assertEqual(command[3], "Perform Action")
                Path(command[-1]).write_bytes(b"test audio")

        runner.run_audio_command = audio_command
        with tempfile.TemporaryDirectory() as directory, patch("gesture_script.Path.home", return_value=Path(directory)):
            runner.speak("  Perform Action  ")
            runner.speak("Perform Action")
            runner.speak("   ")
            self.assertEqual(len(commands), 3)
            self.assertEqual(commands[1][0], "ffplay")
            self.assertEqual(commands[1], commands[2])
            self.assertTrue(Path(commands[1][-1]).is_file())

    def test_readout_then_gesture_grace_and_validation(self):
        from gesture_script import ScriptRunner, parse_script
        events = []
        runner = ScriptRunner(parse_script("[Read: Perform Action] Left Hand Up\n[delay 3 sec]"),
                              speaker=lambda text: events.append(("spoken", text)))
        runner.play_feedback = lambda outcome: events.append(("feedback", outcome))

        def wait(seconds):
            events.append((runner.phase, seconds))
            if runner.phase == "Respond":
                runner.assess(1, {"Left Hand Up"}, [[0, 0, 1] for _ in range(17)], .5)
            runner.drain_feedback()

        runner.wait = wait
        runner.run()
        self.assertIsNone(runner.error)
        self.assertEqual(events, [("spoken", "Perform Action"), ("spoken", "Left Hand Up"),
                                  ("Get ready", 1.0), ("Respond", 3.0),
                                  ("feedback", "success"), ("Result", 1.0)])
        self.assertEqual(runner.results, {1: "Matched"})

    def test_readout_is_not_a_validation_target(self):
        from gesture_script import ScriptRunner, parse_script
        spoken = []
        runner = ScriptRunner(parse_script("[read: Left Hand Up]"), speaker=spoken.append)
        runner.run()
        self.assertIsNone(runner.error)
        self.assertEqual(spoken, ["Left Hand Up"])
        self.assertIsNone(runner.expected)
        with self.assertRaises(ValueError):
            parse_script("[Read: ]")

    def test_recorded_bend_track_change_preserves_success(self):
        from gesture_script import ScriptRunner, parse_script
        runner = ScriptRunner(parse_script("Bend Down\n[delay 3 sec]"), speaker=lambda text: None)
        points = [[0, 0, 1] for _ in range(17)]
        played = []
        runner.play_feedback = played.append

        def wait(seconds):
            if runner.phase == "Respond":
                runner.assess(1, {"Bend Down"}, points, .5,
                              box=(604, 302, 698, 463), timestamp=83.419)
                status, mismatch = runner.assess(17, set(), points, .5,
                                                box=(605, 303, 695, 463), timestamp=84.782)
                self.assertEqual(status, "Matched: Bend Down")
                self.assertFalse(mismatch)
            runner.drain_feedback()

        runner.wait = wait
        runner.run()
        self.assertIsNone(runner.error)
        self.assertEqual(runner.results, {17: "Matched"})
        self.assertEqual(played, ["success"])

    def test_track_reassociation_does_not_merge_unrelated_people(self):
        from gesture_script import ScriptRunner
        points = [[0, 0, 1] for _ in range(17)]
        for box, timestamp, ambiguous in (
            ((800, 302, 894, 463), 84.782, False),
            ((604, 302, 698, 463), 86.0, False),
            ((604, 302, 698, 463), 83.419, False),
            ((604, 302, 698, 463), 84.782, True),
        ):
            with self.subTest(box=box, timestamp=timestamp, ambiguous=ambiguous):
                runner = ScriptRunner([], speaker=lambda text: None)
                runner.expected = "Bend Down"
                runner.phase = "Respond"
                runner.assess(1, {"Bend Down"}, points, .5,
                              box=(604, 302, 698, 463), timestamp=83.419)
                if ambiguous:
                    runner.assess(2, set(), points, .5,
                                  box=(604, 302, 698, 463), timestamp=83.419)
                runner.assess(17, set(), points, .5, box=box, timestamp=timestamp)
                self.assertEqual(runner.observations[17], (False, True))
                self.assertEqual(runner.observations[1], (True, True))

    def test_grace_period_ignores_poses_before_response(self):
        from gesture_script import ScriptRunner, parse_script
        runner = ScriptRunner(parse_script("Hello\nLeft Hand Up\n[delay 3 sec]"), speaker=lambda text: None)
        waits = []
        points = [[0, 0, 1] for _ in range(17)]
        runner.play_feedback = lambda outcome: None

        def wait(seconds):
            waits.append((runner.phase, seconds))
            if runner.phase == "Get ready":
                for label in ("Stand Normal", "Left Hand Up"):
                    self.assertEqual(runner.assess(1, {label}, points, .5), ("", False))
                self.assertEqual(runner.observations, {})
                self.assertEqual(runner.feedback_pending, [])
            elif runner.phase == "Respond":
                runner.assess(1, {"Left Hand Up"}, points, .5)

        runner.wait = wait
        runner.run()
        self.assertIsNone(runner.error)
        self.assertEqual(waits, [("Get ready", 1.0), ("Respond", 3.0), ("Result", 1.0)])
        self.assertEqual(runner.results, {1: "Matched"})

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
    def test_gesture_reference_images_and_split(self):
        from playback import create_player
        player = create_player(30, 100)
        try:
            for width, height in ((1100, 750), (640, 480)):
                player.resize(width, height)
                for gesture in ("Left Hand Up", "Right Hand Up", "Both Hands Up", "Left Leg Up",
                                "Right Leg Up", "Stand Normal", "Bend Down"):
                    player.set_gesture(gesture)
                    player.app.processEvents()
                    player.update_image()
                    self.assertIsNotNone(player.gesture_pixmap, gesture)
                    self.assertAlmostEqual(player.image.width() / player.gesture_image.width(), 3, delta=.03)
                    rendered = player.gesture_image.pixmap()
                    self.assertLessEqual(rendered.width(), player.gesture_image.width())
                    self.assertLessEqual(rendered.height(), player.gesture_image.height())
            for gesture in (None, "Unknown"):
                player.set_gesture(gesture)
                self.assertTrue(player.gesture_image.isHidden())
                self.assertIsNone(player.gesture_pixmap)
        finally:
            player.close()

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