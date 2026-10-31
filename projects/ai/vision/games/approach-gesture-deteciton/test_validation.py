"""Recording-based regression for the two misses in the 2026-10-30 session."""

import unittest
from pathlib import Path

from detect_gestures import GestureState, classify_pose


class RecordedGestureTests(unittest.TestCase):
    def test_recorded_leg_raise_and_forward_bend(self):
        import av
        import torch
        from ultralytics import YOLO

        root = Path(__file__).parent
        video_path = root / "validation" / "session-20261030-194436.mp4"
        model_path = root / "yolo26s-pose.pt"
        self.assertTrue(video_path.is_file(), f"Missing reference video: {video_path}")
        self.assertTrue(model_path.is_file(), f"Missing model weights: {model_path}")
        model = YOLO(str(model_path))
        windows = [
            (39.0, 40.7, None),
            (41.0, 43.9, "Left Leg Up"),
            (78.0, 79.4, None),
            (80.0, 82.6, "Bend Down"),
        ]
        counts = [0] * len(windows)
        confirmed = set()
        states = [GestureState() for _ in windows]
        previous_sample = -1.0
        with av.open(str(video_path)) as video:
            for decoded in video.decode(video=0):
                timestamp = float(decoded.pts * decoded.time_base)
                if timestamp > windows[-1][1]:
                    break
                window_index = next((index for index, (start, end, _) in enumerate(windows)
                                     if start <= timestamp <= end), None)
                if window_index is None or timestamp - previous_sample < .3:
                    continue
                previous_sample = timestamp
                frame = decoded.to_ndarray(format="bgr24")
                result = model(frame, device=0 if torch.cuda.is_available() else "cpu",
                               imgsz=960, verbose=False)[0]
                if not len(result.boxes):
                    continue
                person = int(result.boxes.conf.argmax())
                points = result.keypoints.data[person].cpu().numpy()
                labels, orientation = classify_pose(points)
                counts[window_index] += 1
                expected = windows[window_index][2]
                if expected is None:
                    self.assertFalse({"Left Leg Up", "Bend Down"} & labels,
                                     f"False positive at {timestamp:.2f}s: {labels}")
                else:
                    active = states[window_index].update(labels, orientation, timestamp, .4, .15)
                    if expected in active:
                        confirmed.add(expected)
        self.assertTrue(all(count >= 3 for count in counts), f"Insufficient detections per window: {counts}")
        self.assertEqual(confirmed, {"Left Leg Up", "Bend Down"})


if __name__ == "__main__":
    unittest.main()