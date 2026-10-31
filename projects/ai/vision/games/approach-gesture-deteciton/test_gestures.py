import unittest

from detect_gestures import GestureState, classify_pose, parse_roi


class ConfigTests(unittest.TestCase):
    def test_local_camera_config_and_ssh_commands(self):
        import shlex
        from live_capture import camera_command, LiveCamera, SSHCamera
        args = self.parse_config({'camera-device': '/dev/video2', 'camera-width': 640,
                                  'camera-height': 480, 'camera-fps': 15})
        self.assertIsNone(args.video)
        self.assertIsNone(args.ssh_camera)
        local = camera_command(args.ssh_camera, args.camera_device, args.camera_width,
                               args.camera_height, args.camera_fps)
        self.assertEqual(local[0], 'ffmpeg')
        self.assertEqual(local[local.index('-i') + 1], '/dev/video2')
        self.assertEqual(local[local.index('-video_size') + 1], '640x480')
        self.assertEqual(local[local.index('-framerate') + 1], '15')
        remote = camera_command('ben@10.0.0.226', '/dev/video2', 640, 480, 15)
        self.assertEqual(remote[0], 'ssh')
        self.assertEqual(shlex.split(remote[-1]), local)
        self.assertIs(SSHCamera, LiveCamera)
        with self.assertRaises(ValueError):
            camera_command(None, '/not-a-camera', 640, 480, 15)

    def test_missing_local_camera_fails_before_model_loading(self):
        import contextlib
        import io
        from unittest.mock import patch
        from detect_gestures import main
        errors = io.StringIO()
        with patch('sys.argv', ['detect_gestures.py', '--camera-device', '/dev/video999999']), \
                contextlib.redirect_stderr(errors):
            with self.assertRaises(SystemExit):
                main()
        self.assertIn('Local camera does not exist', errors.getvalue())

    def test_intro_no_skips_both_script_loads_only(self):
        import tempfile
        from pathlib import Path
        from detect_gestures import load_script
        from gesture_script import parse_script
        text = ('[Load:Intro Image][Read:Welcome][Load:Intro Video][delay 5 sec]'
                '[Read:Machee Says] Left Hand Up\n[delay 3 sec][Show Scores][Play Congrats]')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'script.txt'
            path.write_text(text, encoding='utf-8')
            for settings, extra, skip in (({'intro': 'no'}, [], True),
                                           ({'intro': 'yes'}, [], False),
                                           ({'intro': 'yes'}, ['--no-intro'], True)):
                args = self.parse_config(settings, extra)
                with self.subTest(settings=settings, extra=extra):
                    cues = load_script(path, no_intro=args.no_intro)
                    expected = [cue for cue in parse_script(text) if not (skip and cue.kind == 'load')]
                    self.assertEqual(cues, expected)

    def test_session_start_marker_and_script_trimming(self):
        import tempfile
        import json
        from pathlib import Path
        from session_audio import SessionAudio
        from detect_gestures import video_start_seconds, gameplay_cues
        from gesture_script import parse_script
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / 'session.mp4'
            self.assertEqual(video_start_seconds(video), 0)
            audio = SessionAudio(video)
            audio.mark_gameplay_start(99)
            self.assertFalse(video.with_suffix('.session.json').exists())
            audio.started = 100
            audio.mark_gameplay_start(125)
            audio.mark_gameplay_start(140)
            self.assertEqual(video_start_seconds(video), 25)
            self.assertEqual(video_start_seconds(video, 0), 0)
            for invalid in (-1, float('nan'), float('inf'), True, '25'):
                video.with_suffix('.session.json').write_text(json.dumps({'gameplay_start_seconds': invalid}))
                with self.assertRaises(ValueError):
                    video_start_seconds(video)
        cues = parse_script('[Load:Intro Video][Load:Intro Image][Read:Welcome][delay 5 sec]'
                            '[Read:Machee Says] Left Hand Up\n[delay 3 sec][Show Scores][Play Congrats]')
        trimmed = gameplay_cues(cues)
        self.assertEqual(trimmed[0].value, 'Machee Says')
        self.assertEqual(trimmed[1].value, 'Left Hand Up')
        self.assertEqual(trimmed[-1].value, 'play congrats')
        self.assertFalse(any(cue.kind == 'load' for cue in trimmed))

    def parse_config(self, settings, extra=()):
        import json
        import tempfile
        from pathlib import Path
        from detect_gestures import build_parser, parse_arguments
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(settings))
            return parse_arguments(build_parser(), ["--config", str(path), *extra])

    def test_config_types_and_cli_overrides(self):
        from pathlib import Path
        args = self.parse_config({
            "video": "input.mp4", "camera-width": 640, "confidence": .6,
            "roi": "0,0;10,0;10,10", "skeleton": True, "no_intro": True,
            "show": False, "tts": "gtts", "device": "0",
            "output": "output/session-{timestamp}.mp4",
        }, ["--device", "cpu", "--camera-width", "1280", "--show", "replacement.mp4"])
        self.assertEqual(args.video, Path("replacement.mp4"))
        self.assertEqual(args.camera_width, 1280)
        self.assertEqual(args.device, "cpu")
        self.assertEqual(args.confidence, .6)
        self.assertEqual(args.roi, [(0, 0), (10, 0), (10, 10)])
        self.assertTrue(args.skeleton and args.no_intro and args.show)
        self.assertRegex(str(args.output), r"^output/session-\d{8}-\d{6}\.mp4$")
        self.assertEqual(self.parse_config({"video": "input.mp4"}).video, Path("input.mp4"))

    def test_invalid_config_rejected(self):
        self.assertFalse(self.parse_config({"intro": "yes"}).no_intro)
        self.assertTrue(self.parse_config({"intro": "no"}).no_intro)
        self.assertTrue(self.parse_config({"intro": "yes"}, ["--no-intro"]).no_intro)
        import contextlib
        import io
        for settings in ([], {"intro": True}, {"intro": "maybe"}, {"intro": "yes", "no-intro": True},
                 {"unknown": 1}, {"show": "false"}, {"camera-fps": "bad"},
                         {"tts": "invalid"}, {"roi": "bad"}, {"device": None},
                         {"no-intro": True, "no_intro": False}, {"config": "nested.json"}):
            with self.subTest(settings=settings), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    self.parse_config(settings)


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
        for displacement, accepted in ((24, True), (-24, True), (36, False), (-36, False)):
            relaxed = [point[:] for point in points]
            relaxed[8][0] += displacement / 2
            relaxed[10][0] += displacement
            with self.subTest(wrist_displacement=displacement):
                self.assertEqual("Stand Normal" in classify_pose(relaxed)[0], accepted)
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
    def test_color_pattern_handles_pose_shift(self):
        import numpy as np
        from gesture_script import ScriptRunner
        upright = np.full((220, 100, 3), 180, dtype=np.uint8)
        upright[20:90, 20:80] = (30, 190, 220)
        upright[90:180, 20:80] = (45, 180, 35)
        shifted = np.full_like(upright, 180)
        shifted[40:110, 10:70] = (30, 190, 220)
        shifted[110:200, 10:70] = (45, 180, 35)
        different = shifted.copy()
        different[110:200, 10:70] = (190, 50, 30)
        self.assertTrue(ScriptRunner.color_pattern_match(upright, shifted))
        self.assertFalse(ScriptRunner.color_pattern_match(upright, different))
        self.assertFalse(ScriptRunner.color_pattern_match(upright, upright[::-1].copy()))
        self.assertFalse(ScriptRunner.color_pattern_match(upright, None))
        flat = np.full_like(upright, (30, 190, 220))
        self.assertFalse(ScriptRunner.color_pattern_match(flat, flat))
        runner = ScriptRunner([], speaker=lambda text: None)
        for track_id, correct, photo in ((1, 10, shifted), (2, 6, upright), (3, 5, different)):
            runner.participants[track_id] = {"correct": correct, "total": 10, "photo": photo}
        self.assertEqual([row["track_id"] for row in runner.scores()], [1, 3])

    def test_tamil_gestures_keep_original_speech_and_game_rules(self):
        from gesture_script import ScriptRunner, parse_script, gesture_name, is_machee_says
        from detect_gestures import gameplay_cues
        import unicodedata
        self.assertTrue(is_machee_says('மாச்சி சொல்கிறார்'))
        self.assertEqual(gesture_name(unicodedata.normalize('NFD', 'இடது காலை மேலே தூக்கு')), 'Left Leg Up')
        cues = gameplay_cues(parse_script('[Load:Intro Image][Read:Welcome][delay 5 sec]'
                                         '[Read: மச்சி சொல்கிறார்] இடது கையை உயர்த்தவும்\n'
                                         'வலது கையை உயர்த்தவும்\n'
                                         '[Read: மச்சி சொல்கிறார்] சாதாரணமாக நில்'))
        seen = []
        runner = ScriptRunner(cues, speaker=lambda text: seen.append(
            (text, runner.expected, runner.gesture_image(), runner.hold_previous)))
        runner.wait = lambda seconds: None
        runner.run()
        self.assertIsNone(runner.error)
        self.assertTrue(runner.machee_says)
        self.assertEqual(seen[0][2], 'Left Hand Up')
        self.assertEqual(seen[1], ('இடது கையை உயர்த்தவும்', 'Left Hand Up', 'Left Hand Up', False))
        self.assertEqual(seen[2], ('வலது கையை உயர்த்தவும்', 'Left Hand Up', 'Left Hand Up', True))
        self.assertEqual(seen[3][2], 'Stand Normal')
        self.assertEqual(seen[4], ('சாதாரணமாக நில்', 'Stand Normal', 'Stand Normal', False))

    def test_partial_image_match_keeps_higher_score(self):
        import cv2
        import numpy as np
        from gesture_script import ScriptRunner
        generator = np.random.default_rng(23)
        first = generator.integers(0, 256, (288, 96, 3), dtype=np.uint8)
        partial = generator.integers(0, 256, first.shape, dtype=np.uint8)
        template = cv2.resize(first[:144, 12:84], None, fx=.6, fy=.6)
        height, width = template.shape[:2]
        partial[19:19 + height, 6:6 + width] = template
        different = generator.integers(0, 256, first.shape, dtype=np.uint8)
        different[:, :, 0] //= 4
        self.assertTrue(ScriptRunner.partial_image_match(first, partial))
        self.assertTrue(ScriptRunner.partial_image_match(partial, first))
        self.assertFalse(ScriptRunner.partial_image_match(first, different))
        self.assertFalse(ScriptRunner.partial_image_match(first, None))
        runner = ScriptRunner([], speaker=lambda text: None)
        for track_id, correct, photo in ((5, 0, partial), (4, 6, first), (3, 3, different)):
            runner.participants[track_id] = {"correct": correct, "total": 10, "photo": photo}
        self.assertEqual([row["track_id"] for row in runner.scores()], [4, 3])

    def test_majority_pixels_with_partial_occlusion(self):
        import numpy as np
        from gesture_script import ScriptRunner
        generator = np.random.default_rng(42)
        first = generator.integers(0, 256, (96, 48, 3), dtype=np.uint8)
        second = first.copy()
        second[:35] = 0
        self.assertGreater(ScriptRunner.majority_pixel_agreement(first, second), .5)
        second[:70] = 0
        self.assertLess(ScriptRunner.majority_pixel_agreement(first, second), .5)
        shifted = np.zeros_like(first)
        shifted[4:, 2:] = first[:-4, :-2]
        self.assertGreater(ScriptRunner.majority_pixel_agreement(first, shifted), .85)

    def test_clothing_match_survives_arm_pose_change(self):
        import numpy as np
        from gesture_script import ScriptRunner
        first = np.full((180, 90, 3), 180, dtype=np.uint8)
        first[35:96, 18:72] = (35, 185, 210)
        first[98:165, 18:72] = (70, 155, 40)
        changed_pose = first.copy()
        changed_pose[:100, :18] = (50, 95, 150)
        changed_pose[35:90, 38:48] = (50, 95, 150)
        different_trousers = changed_pose.copy()
        different_trousers[98:165, 18:72] = (190, 50, 40)
        runner = ScriptRunner([], speaker=lambda text: None)
        for track_id, correct, photo in ((1, 2, changed_pose), (2, 9, first), (3, 3, different_trousers)):
            runner.participants[track_id] = {"correct": correct, "total": 10, "photo": photo}
        self.assertEqual([row["track_id"] for row in runner.scores()], [2, 3])

    def test_duplicate_photos_keep_highest_score_only(self):
        import cv2
        import numpy as np
        from gesture_script import ScriptRunner
        photo = np.full((180, 90, 3), 45, dtype=np.uint8)
        photo[15:55, 25:65] = (90, 140, 180)
        photo[55:125, 15:75] = (130, 60, 30)
        photo[125:170, 20:40] = (25, 25, 25)
        similar = cv2.resize(cv2.convertScaleAbs(photo, alpha=1, beta=9), (120, 240))
        distinct = photo.copy()
        distinct[55:125, 15:75] = (35, 120, 70)
        different_pattern = photo[::-1].copy()
        runner = ScriptRunner([], speaker=lambda text: None)
        for track_id, correct, image in ((1, 5, photo), (2, 9, similar), (3, 2, photo.copy()),
                                         (4, 7, distinct), (5, 9, similar.copy()),
                                         (6, 6, different_pattern), (7, 0, None), (8, 0, None)):
            runner.participants[track_id] = {"correct": correct, "total": 10, "photo": image}
        self.assertEqual([row["track_id"] for row in runner.scores()], [2, 4, 6, 7, 8])
        self.assertEqual(len(runner.participants), 8)
        self.assertEqual(runner.participants[2]["correct"], 9)

    def test_score_bands_and_verifiable_rounds(self):
        from gesture_script import ScriptRunner
        runner = ScriptRunner([], speaker=lambda text: None)
        for track_id, correct, total in ((1, 90, 100), (2, 89, 100), (3, 50, 100),
                                         (4, 49, 100), (5, 0, 100), (6, 0, 0), (7, 100, 100)):
            runner.participants[track_id] = {"correct": correct, "total": total, "photo": None}
        self.assertEqual({row["track_id"]: row["medal"] for row in runner.scores()},
                         {1: "Gold", 2: "Silver", 3: "Silver", 4: "Bronze", 5: "Bronze", 6: "Unscored", 7: "Gold"})
        runner.results = {1: "Matched", 2: "Matched", 3: "Not performed", 6: "Cannot verify"}
        runner.round_mistakes.add(2)
        runner.score_round()
        runner.score_round()
        self.assertEqual(runner.participants[1]["correct"], 91)
        self.assertEqual(runner.participants[2]["correct"], 89)
        self.assertEqual(runner.participants[2]["total"], 101)
        self.assertEqual(runner.participants[3]["total"], 101)
        self.assertEqual(runner.participants[6]["total"], 0)

    def test_score_and_congratulations_directives_are_not_spoken(self):
        from gesture_script import ScriptRunner, parse_script
        spoken, requests = [], []
        runner = ScriptRunner(parse_script("[Show Scores] [Play Congrats]"), speaker=spoken.append)

        def complete(timeout):
            requests.append(runner.take_video_request())
            return True

        runner.video_done.wait = complete
        runner.run()
        self.assertIsNone(runner.error)
        self.assertEqual(spoken, [])
        self.assertEqual(requests, ["show scores", "play congrats"])

    def test_scripted_intro_waits_before_welcome(self):
        import threading
        from gesture_script import ScriptRunner, parse_script
        spoken = []
        waiting = threading.Event()
        runner = ScriptRunner(parse_script(
            "[Load:Intro Video]\n[Load:Intro Image][Read:Welcome]\n[delay 5 sec]"),
            speaker=lambda text: None)
        runner.speaker = lambda text: spoken.append((text, runner.gesture_image()))
        runner.wait = lambda seconds: None
        original_wait = runner.video_done.wait

        def wait_for_video(timeout):
            waiting.set()
            return original_wait(timeout)

        runner.video_done.wait = wait_for_video
        runner.thread.start()
        try:
            self.assertTrue(waiting.wait(2))
            self.assertEqual(spoken, [])
            self.assertEqual(runner.take_video_request(), "Intro Video")
            self.assertIsNone(runner.take_video_request())
            runner.video_done.set()
            runner.thread.join(timeout=2)
            self.assertFalse(runner.thread.is_alive())
            self.assertIsNone(runner.error)
            self.assertEqual(spoken, [("Welcome", "Intro Image")])
        finally:
            runner.close()

    def test_load_intro_image_with_readout(self):
        from gesture_script import ScriptRunner, parse_script
        observed = []
        runner = ScriptRunner(parse_script(
            "[Load:Intro Image][Read:Welcome]\n[delay 5 sec]\n[Read: Machee Says] Left Hand Up"),
            speaker=lambda text: None)
        runner.speaker = lambda text: observed.append((text, runner.gesture_image()))
        runner.wait = lambda seconds: observed.append((seconds, runner.gesture_image()))
        runner.run()
        self.assertIsNone(runner.error)
        self.assertEqual(observed, [("Welcome", "Intro Image"), (5.0, "Intro Image"),
                                    ("Machee Says", "Left Hand Up"), ("Left Hand Up", "Left Hand Up"),
                                    (1.0, "Left Hand Up")])
        with self.assertRaises(ValueError):
            parse_script("[Load:Unknown]")

    def test_corrected_mistake_still_shows_failure_review(self):
        import numpy as np
        from gesture_script import ScriptRunner, parse_script
        runner = ScriptRunner(parse_script("Right Leg Up\n[delay 3 sec]"),
                              speaker=lambda text: None, failure_screen=True)
        runner.play_feedback = lambda outcome: None
        runner.failure_done.wait = lambda timeout: True
        points = [[0, 0, 1] for _ in range(17)]
        frame = np.full((20, 20, 3), 123, dtype=np.uint8)

        def wait(seconds):
            if runner.phase == "Respond":
                runner.assess(1, {"Right Leg Up"}, points, .5,
                              box=(50, 0, 70, 20), timestamp=1, frame=frame)
                runner.assess(2, {"Stand Normal"}, points, .5,
                              box=(0, 0, 20, 20), timestamp=1, frame=frame)
                runner.assess(3, {"Right Leg Up"}, points, .5,
                              box=(0, 0, 20, 20), timestamp=1.5, frame=frame * 0)

        runner.wait = wait
        runner.run()
        self.assertIsNone(runner.error)
        self.assertEqual(runner.results, {1: "Matched", 3: "Matched"})
        expected, failed = runner.take_failure_request()
        self.assertEqual(expected, "Right Leg Up")
        self.assertEqual(set(failed), {3})
        self.assertTrue((failed[3] == 123).all())

    def test_machee_says_hold_previous_pose(self):
        from gesture_script import ScriptRunner, parse_script
        import numpy as np
        for change in (False, True):
            with self.subTest(change=change):
                runner = ScriptRunner(parse_script(
                    "[Read: Machee Says] Right Leg Up\n[delay 3 sec]\nStand Normal\n[delay 3 sec]"),
                    speaker=lambda text: None)
                runner.play_feedback = lambda outcome: None
                points = [[0, 0, 1] for _ in range(17)]
                frame = np.full((20, 20, 3), 100, dtype=np.uint8)

                def wait(seconds):
                    if runner.phase != "Respond":
                        return
                    runner.assess(1, {"Right Leg Up"}, points, .5,
                                  box=(0, 0, 20, 20), timestamp=1, frame=frame)
                    if runner.hold_previous:
                        self.assertEqual(runner.expected, "Right Leg Up")
                        self.assertEqual(runner.gesture_image(), "Right Leg Up")
                        self.assertEqual(runner.feedback_pending, [])
                        if change:
                            runner.assess(1, {"Stand Normal"}, points, .5,
                                          box=(0, 0, 20, 20), timestamp=1.2, frame=frame)
                            runner.assess(2, {"Right Leg Up"}, points, .5,
                                          box=(0, 0, 20, 20), timestamp=1.5, frame=frame * 0)

                runner.wait = wait
                runner.run()
                self.assertIsNone(runner.error)
                self.assertEqual(runner.results, {2: "Not performed"} if change else {1: "Matched"})
                if change:
                    self.assertTrue((runner.person_frames[2] == 100).all())

    def test_machee_says_only_authorizes_next_command(self):
        from gesture_script import ScriptRunner, parse_script
        observed = []
        runner = ScriptRunner(parse_script(
            "[Read: Machee Says] Left Hand Up\n[delay 3 sec]\n"
            "[Read: Perform Action] Right Hand Up\n[delay 3 sec]\n"
            "[Read: Machee Says] Stand Normal\n[delay 3 sec]"), speaker=lambda text: None)
        runner.wait = lambda seconds: observed.append((runner.expected, runner.hold_previous)) if runner.phase == "Respond" else None
        runner.run()
        self.assertIsNone(runner.error)
        self.assertEqual(observed, [("Left Hand Up", False), ("Left Hand Up", True), ("Stand Normal", False)])

    def test_failure_review_crops_and_blocks_next_prompt(self):
        import threading
        import time
        import numpy as np
        from gesture_script import ScriptRunner, parse_script
        spoken = []
        runner = ScriptRunner(parse_script("Left Hand Up\n[delay 3 sec]\nThanks"),
                              speaker=spoken.append, failure_screen=True)
        frame = np.full((80, 100, 3), 123, dtype=np.uint8)
        points = [[0, 0, 1] for _ in range(17)]
        runner.play_feedback = lambda outcome: None

        def wait(seconds):
            if runner.phase == "Respond":
                runner.assess(1, set(), points, .5, box=(0, 0, 40, 60), timestamp=1, frame=frame)
                runner.assess(2, {"Left Hand Up"}, points, .5, box=(50, 0, 100, 60), timestamp=1, frame=frame)
                runner.assess(3, set(), [[0, 0, 0] for _ in range(17)], .5,
                              box=(0, 0, 20, 30), timestamp=1, frame=frame)
                frame[:] = 0

        runner.wait = wait
        runner.thread.start()
        try:
            deadline = time.monotonic() + 2
            request = None
            while request is None and time.monotonic() < deadline:
                request = runner.take_failure_request()
                threading.Event().wait(.01)
            self.assertIsNotNone(request)
            expected, failed = request
            self.assertEqual(expected, "Left Hand Up")
            self.assertEqual(set(failed), {1})
            self.assertEqual(failed[1].shape, (60, 40, 3))
            self.assertTrue((failed[1] == 123).all())
            self.assertEqual(spoken, ["Left Hand Up"])
            runner.failure_done.set()
            runner.thread.join(timeout=2)
            self.assertFalse(runner.thread.is_alive())
            self.assertEqual(spoken, ["Left Hand Up", "Thanks"])
        finally:
            runner.close()

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
    def test_scores_saved_separately_for_each_session(self):
        import tempfile
        from pathlib import Path
        import numpy as np
        from PySide6.QtGui import QImage
        from playback import create_player
        entries = [{"track_id": 4, "correct": 6, "total": 10, "percentage": 60,
                    "medal": "Silver", "photo": np.full((100, 60, 3), 180, dtype=np.uint8)}]
        player = create_player(30, 100, live=True)
        try:
            with tempfile.TemporaryDirectory() as directory:
                first = Path(directory) / 'output' / 'session-1.scores.png'
                second = first.with_name('session-2.scores.png')
                player.show_scores(entries, save_path=first)
                original = first.read_bytes()
                player.show_scores([], save_path=second)
                self.assertEqual(first.read_bytes(), original)
                self.assertNotEqual(second.read_bytes(), original)
                image = QImage(str(first))
                self.assertFalse(image.isNull())
                self.assertEqual(image.size(), player.image.size())
                self.assertFalse(first.with_suffix('.tmp.png').exists())
        finally:
            player.close()

    def test_tamil_gestures_load_existing_images(self):
        from gesture_script import gesture_name
        from playback import create_player
        mappings = {'இடது கையை உயர்த்தவும்': 'Left Hand Up', 'வலது கையை உயர்த்தவும்': 'Right Hand Up',
                    'இரு கைகளையும் உயர்த்தவும்': 'Both Hands Up', 'இடது காலை மேலே தூக்கு': 'Left Leg Up',
                    'வலது காலை மேலே தூக்கு': 'Right Leg Up', 'சாதாரணமாக நில்': 'Stand Normal',
                    'குனியுங்கள்': 'Bend Down'}
        player = create_player(30, 100, live=True)
        try:
            for text, expected in mappings.items():
                with self.subTest(text=text):
                    self.assertEqual(gesture_name(text), expected)
                    player.set_gesture(gesture_name(text))
                    self.assertIsNotNone(player.gesture_pixmap)
                    self.assertFalse(player.gesture_pixmap.isNull())
        finally:
            player.close()

    def test_scores_persist_during_congratulations(self):
        from unittest.mock import patch, MagicMock
        from types import SimpleNamespace
        from pathlib import Path
        import numpy as np
        from playback import create_player
        player = create_player(30, 100, live=True)
        entries = [{"track_id": 1, "correct": 9, "total": 10, "percentage": 90,
                    "medal": "Gold", "photo": np.full((100, 60, 3), 180, dtype=np.uint8)}]
        decoded = SimpleNamespace(time=0, to_ndarray=lambda **kwargs: np.zeros((60, 80, 3), dtype=np.uint8))
        video = MagicMock()
        video.__enter__.return_value = video
        video.decode.return_value = iter([decoded])
        video.duration = 0
        player.session_audio = MagicMock()
        try:
            player.show_scores(entries)
            with patch("playback.Path.glob", return_value=iter([Path("congrats/test.mp4")])), \
                    patch("av.open", return_value=video), patch("playback.subprocess.Popen"):
                player.show_failures(None, {}, congrats=True)
            player.display(np.zeros((60, 80, 3), dtype=np.uint8), 0)
            self.assertEqual(player.score_entries, entries)
            self.assertFalse(player.render_scores().isNull())
            self.assertEqual(player.error.text(), "")
            self.assertEqual(player.session_audio.record.call_args.args[0][-1], "congrats/test.mp4")
        finally:
            player.close()

    def test_presentation_recording_runs_without_camera_updates(self):
        from unittest.mock import MagicMock
        from PySide6.QtTest import QTest
        from playback import create_player
        player = create_player(30, 100, live=True)
        writer, audio = MagicMock(), MagicMock()
        audio.started = None
        try:
            player.set_gesture("Intro Image")
            player.start_recording(writer, audio, 640, 360, 30)
            QTest.qWait(100)
            audio.mark_gameplay_start.assert_not_called()
            player.gameplay_visible = True
            player.record_presentation()
            audio.mark_gameplay_start.assert_not_called()
            player.set_gesture("Left Hand Up")
            player.record_presentation()
            audio.mark_gameplay_start.assert_called_once_with(writer.write.call_args.args[1])
            player.stop_recording()
            self.assertIsNone(player.recording_error)
            self.assertGreaterEqual(writer.write.call_count, 2)
            frames = writer.write.call_args_list
            self.assertEqual(frames[-1].args[0].shape, (360, 640, 3))
            self.assertGreater(frames[-1].args[0].max(), 100)
            self.assertEqual(audio.started, frames[0].args[1])
            self.assertGreater(frames[-1].args[1], frames[0].args[1])
            count = writer.write.call_count
            QTest.qWait(50)
            self.assertEqual(writer.write.call_count, count)
        finally:
            player.close()

    def test_intro_image_persists_over_camera_frames(self):
        import numpy as np
        from playback import create_player
        player = create_player(30, 100, live=True)
        try:
            player.set_gesture("Intro Image")
            player.display(np.zeros((60, 80, 3), dtype=np.uint8), 0)
            self.assertIsNotNone(player.intro_image)
            self.assertFalse(player.intro_image.isNull())
            self.assertTrue(player.gesture_image.isHidden())
            self.assertGreater(player.image.pixmap().width(), 0)
            player.set_gesture("Left Hand Up")
            self.assertIsNone(player.intro_image)
            self.assertFalse(player.gesture_image.isHidden())
        finally:
            player.close()

    def test_failure_clip_completion_restores_player(self):
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import patch, MagicMock
        import numpy as np
        from playback import create_player
        player = create_player(30, 100)
        player.set_gesture("Left Hand Up")
        player.session_audio = MagicMock()
        decoded = SimpleNamespace(time=0, to_ndarray=lambda **kwargs: np.zeros((60, 100, 3), dtype=np.uint8)[:, :80])
        video = MagicMock()
        video.__enter__.return_value = video
        video.decode.return_value = iter([decoded])
        video.duration = 0
        process = MagicMock()
        process.poll.return_value = None
        try:
            with patch("playback.Path.glob", return_value=iter([Path("bad/example.mp4")])), \
                    patch("av.open", return_value=video), \
                    patch("playback.subprocess.Popen", return_value=process) as audio:
                player.show_failures("Left Hand Up", {1: np.ones((80, 60, 3), dtype=np.uint8)})
            self.assertEqual(player.error.text(), "")
            self.assertEqual(player.current_gesture, "Left Hand Up")
            self.assertTrue(player.play.isEnabled())
            self.assertIn("-vn", audio.call_args.args[0])
            player.session_audio.record.assert_called_once()
            self.assertEqual(player.session_audio.record.call_args.args[0], audio.call_args.args[0])
            process.terminate.assert_called_once()
        finally:
            player.close()

    def test_intro_playback_command(self):
        from unittest.mock import patch, MagicMock
        from detect_gestures import play_intro
        player = MagicMock()
        with patch("detect_gestures.Path.is_file", return_value=True), \
                patch("detect_gestures.shutil.which", return_value="ffplay"):
            play_intro(player)
            self.assertEqual(player.show_failures.call_args.args, (None, {}))
            self.assertTrue(str(player.show_failures.call_args.kwargs["intro_clip"]).endswith("/intro/1.mp4"))

    def test_intro_retains_fullscreen_image_until_camera_frame(self):
        from unittest.mock import patch, MagicMock
        from types import SimpleNamespace
        from pathlib import Path
        import numpy as np
        from playback import create_player
        player = create_player(30, 100, live=True)
        decoded = SimpleNamespace(time=0, to_ndarray=lambda **kwargs: np.full((60, 80, 3), 123, dtype=np.uint8))
        video = MagicMock()
        video.__enter__.return_value = video
        video.decode.return_value = iter([decoded])
        video.duration = 0
        try:
            with patch("av.open", return_value=video), patch("playback.subprocess.Popen"):
                player.show_failures(None, {}, intro_clip=Path("intro/1.mp4"))
            self.assertTrue(player.isFullScreen())
            self.assertFalse(player.pixmap.isNull())
            self.assertEqual(player.pixmap.toImage().pixelColor(0, 0).red(), 123)
            self.assertTrue(player.gesture_image.isHidden())
            player.display(np.zeros((60, 80, 3), dtype=np.uint8), 0)
            self.assertTrue(player.isFullScreen())
            self.assertEqual(player.pixmap.toImage().pixelColor(0, 0).red(), 0)
        finally:
            player.close()

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