"""Track people and annotate rule-based gestures in a local video."""

from __future__ import annotations

import argparse
import csv
import math
from contextlib import nullcontext
from pathlib import Path


def classify_pose(points, confidence=0.5):
    def visible(*indices):
        return all(points[index][2] >= confidence for index in indices)

    labels = set()
    if not visible(5, 6, 11, 12):
        return labels, "Unknown"
    shoulder = [(points[5][axis] + points[6][axis]) / 2 for axis in (0, 1)]
    hip = [(points[11][axis] + points[12][axis]) / 2 for axis in (0, 1)]
    torso = math.dist(shoulder, hip)
    if torso < 5:
        return labels, "Unknown"
    raised = []
    for side, wrist, elbow, joint in (("Left", 9, 7, 5), ("Right", 10, 8, 6)):
        if visible(wrist, elbow, joint) and points[wrist][1] < points[joint][1] - torso * 0.2:
            raised.append(f"{side} Hand Up")
    labels.update(["Both Hands Up"] if len(raised) == 2 else raised)
    for side, knee, ankle, other_ankle in (("Left", 13, 15, 16), ("Right", 14, 16, 15)):
        if visible(knee, ankle, other_ankle):
            if points[ankle][1] < points[other_ankle][1] - torso * 0.35 and points[knee][1] < hip[1] + torso * 0.45:
                labels.add(f"{side} Leg Up")
    lean = math.degrees(math.atan2(abs(shoulder[0] - hip[0]), hip[1] - shoulder[1]))
    if lean > 50:
        labels.add("Bend Down")
    orientation = "Unknown"
    if visible(0, 1, 2):
        width = abs(points[5][0] - points[6][0])
        offset = (points[0][0] - shoulder[0]) / max(width, torso * 0.25)
        if offset < -0.35:
            orientation = "Screen Left"
        elif offset > 0.35:
            orientation = "Screen Right"
        else:
            orientation = "Front"
    return labels, orientation


class GestureState:
    def __init__(self):
        self.started = {}
        self.last_seen = {}
        self.orientation = "Unknown"
        self.orientation_since = 0.0
        self.stable_orientation = "Unknown"
        self.turn_label = None
        self.turn_until = 0.0

    def update(self, labels, orientation, timestamp, hold, release, turns=False):
        for label in labels:
            self.started.setdefault(label, timestamp)
            self.last_seen[label] = timestamp
        for label in list(self.started):
            if timestamp - self.last_seen[label] > release:
                del self.started[label]
                del self.last_seen[label]
        active = {label for label in self.started if self.last_seen[label] - self.started[label] >= hold}
        if "Both Hands Up" in active:
            active.difference_update({"Left Hand Up", "Right Hand Up"})
        if orientation != self.orientation:
            self.orientation = orientation
            self.orientation_since = timestamp
        if orientation != "Unknown" and timestamp - self.orientation_since >= hold:
            if turns and self.stable_orientation == "Front" and orientation in ("Screen Left", "Screen Right"):
                self.turn_label = "Turn Right" if orientation == "Screen Left" else "Turn Left"
                self.turn_until = timestamp + 1.0
            self.stable_orientation = orientation
        if turns and timestamp < self.turn_until and self.turn_label:
            active.add(self.turn_label)
        return active


def parse_roi(value):
    try:
        vertices = [tuple(map(int, pair.split(","))) for pair in value.split(";")]
        if len(vertices) < 3 or any(len(vertex) != 2 for vertex in vertices):
            raise ValueError
        return vertices
    except ValueError as error:
        raise argparse.ArgumentTypeError('Use at least three pixel points: "100,200;500,200;500,600"') from error


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="Input MP4 or other OpenCV-readable video")
    parser.add_argument("--output", type=Path, help="Optionally save MP4 and CSV; default is display only")
    parser.add_argument("--model", default="yolo26s-pose.pt")
    parser.add_argument("--device", default="auto", help="auto, cpu, or CUDA index such as 0")
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--confidence", type=float, default=0.35, help="Person detection threshold")
    parser.add_argument("--keypoint-confidence", type=float, default=0.5)
    parser.add_argument("--hold", type=float, default=0.4, help="Gesture confirmation duration in seconds")
    parser.add_argument("--release", type=float, default=0.15, help="Tolerance for brief missing observations")
    parser.add_argument("--roi", type=parse_roi, help="Near-vehicle ground polygon in source-image pixels")
    parser.add_argument("--skeleton", action="store_true")
    parser.add_argument("--show", action="store_true", help="Display preview; press q to stop")
    parser.add_argument("--experimental-turns", action="store_true", help="Enable approximate front-to-side turn events")
    parser.add_argument("--max-frames", type=int, default=0, help="Stop after this many frames; 0 processes all")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.video.is_file():
        parser.error(f"Video does not exist: {args.video}")
    if args.hold <= 0 or args.release < 0 or args.imgsz <= 0 or args.max_frames < 0:
        parser.error("hold/imgsz must be positive; release/max-frames must be nonnegative")
    if not all(0 < threshold <= 1 for threshold in (args.confidence, args.keypoint_confidence)):
        parser.error("Confidence thresholds must be in (0, 1]")
    output = args.output
    show = args.show or output is None
    if output is not None and output.suffix.lower() != ".mp4":
        parser.error("Output must have an .mp4 extension")
    csv_path = output.with_suffix(".csv") if output is not None else None
    if output is not None and args.video.resolve() in (output.resolve(), csv_path.resolve()):
        parser.error("Output must not overwrite the input")
    if output is not None and (output.exists() or csv_path.exists()):
        parser.error("Output MP4 or CSV already exists; choose a different --output")

    import cv2
    import numpy as np
    import torch
    from ultralytics import YOLO

    device = (0 if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    if str(device) != "cpu" and not torch.cuda.is_available():
        parser.error("CUDA unavailable; use --device cpu or install a compatible GPU PyTorch build")
    print(f"Device: {device}; model: {args.model}")
    print("Turn Back is not inferred from missing face landmarks. Turn Left/Right require --experimental-turns.")
    model = YOLO(args.model)
    if model.task != "pose":
        parser.error("Choose a YOLO pose model")
    capture = cv2.VideoCapture(str(args.video))
    writer = None
    frame_index = 0
    try:
        if not capture.isOpened():
            raise RuntimeError(f"Cannot decode {args.video}")
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps <= 0:
            raise RuntimeError("Video FPS is invalid; transcode to a constant-frame-rate MP4 first")
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
            if not writer.isOpened():
                raise RuntimeError("Could not open MP4 encoder")
        if show:
            cv2.namedWindow("Gesture detection", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Gesture detection", min(width, 1280), min(height, 720))
        polygon = np.array(args.roi, dtype=np.int32) if args.roi else None
        states = {}
        seen = {}
        with (csv_path.open("w", newline="") if csv_path is not None else nullcontext()) as csv_file:
            log = csv.writer(csv_file) if csv_file is not None else None
            if log is not None:
                log.writerow(["frame", "seconds", "track_id", "gestures", "orientation_hint", "near_vehicle", "x1", "y1", "x2", "y2"])
            while not args.max_frames or frame_index < args.max_frames:
                success, frame = capture.read()
                if not success:
                    break
                timestamp = frame_index / fps
                result = model.track(frame, persist=True, tracker="bytetrack.yaml", device=device,
                                     imgsz=args.imgsz, conf=args.confidence, verbose=False)[0]
                canvas = result.plot(boxes=False, labels=False, conf=False) if args.skeleton else frame.copy()
                if polygon is not None:
                    cv2.polylines(canvas, [polygon], True, (0, 200, 220), 2)
                if result.boxes is not None and result.keypoints is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    poses = result.keypoints.data.cpu().numpy()
                    identities = result.boxes.id.int().cpu().tolist() if result.boxes.is_track else [None] * len(boxes)
                    for box, points, track_id in zip(boxes, poses, identities):
                        left, top, right, bottom = map(int, box)
                        raw_labels, orientation = classify_pose(points, args.keypoint_confidence)
                        active = set()
                        if track_id is not None:
                            if timestamp - seen.get(track_id, timestamp) > args.release:
                                states.pop(track_id, None)
                            state = states.setdefault(track_id, GestureState())
                            active = state.update(raw_labels, orientation, timestamp, args.hold, args.release, args.experimental_turns)
                            seen[track_id] = timestamp
                        near = "Not configured"
                        if polygon is not None:
                            near = "Unknown"
                            if points[15][2] >= args.keypoint_confidence and points[16][2] >= args.keypoint_confidence:
                                foot = tuple(map(float, (points[15][:2] + points[16][:2]) / 2))
                                near = "Yes" if cv2.pointPolygonTest(polygon, foot, False) >= 0 else "No"
                        pose_visible = all(points[index][2] >= args.keypoint_confidence for index in (5, 6, 9, 10, 11, 12, 13, 14, 15, 16))
                        label = ", ".join(sorted(active)) or ("No listed gesture" if pose_visible else "Unknown")
                        text = f"ID {track_id if track_id is not None else '?'} | {label}"
                        if polygon is not None:
                            text += f" | Near vehicle: {near}"
                        color = (0, 180, 255) if active else (80, 210, 80)
                        cv2.rectangle(canvas, (left, top), (right, bottom), color, 2)
                        scale = min(0.6, max(0.2, (width - 10) / max(1, cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 1)[0][0])))
                        text_width, text_height = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)[0]
                        text_left = max(0, min(left, width - text_width - 6))
                        baseline = max(text_height + 6, min(top - 6, height - 6))
                        cv2.rectangle(canvas, (text_left, baseline - text_height - 4), (text_left + text_width + 4, baseline + 4), (20, 20, 20), -1)
                        cv2.putText(canvas, text, (text_left + 2, baseline), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)
                        if log is not None:
                            log.writerow([frame_index, f"{timestamp:.3f}", track_id, label, orientation, near, left, top, right, bottom])
                for track_id in list(seen):
                    if timestamp - seen[track_id] > 2:
                        del seen[track_id]
                        states.pop(track_id, None)
                if writer is not None:
                    writer.write(canvas)
                frame_index += 1
                if frame_index % 100 == 0:
                    print(f"Processed {frame_index} frames ({frame_index / fps:.1f}s of video)", flush=True)
                if show:
                    cv2.imshow("Gesture detection", canvas)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord("q"), 27) or cv2.getWindowProperty("Gesture detection", cv2.WND_PROP_VISIBLE) < 1:
                        break
        if frame_index == 0:
            raise RuntimeError("No video frames decoded")
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        if show:
            cv2.destroyAllWindows()
    if output is not None:
        print(f"Saved {frame_index} frames: {output}\nLabels: {csv_path}\nOutput video has no audio.")
    else:
        print(f"Displayed {frame_index} frames. No output files saved.")


if __name__ == "__main__":
    main()