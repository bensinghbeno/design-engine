"""Track people and annotate rule-based gestures in a local video."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
import csv
import math
import time
import logging
import shutil
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
            if points[ankle][1] < points[other_ankle][1] - torso * 0.28 and points[knee][1] < hip[1] + torso * 0.8:
                labels.add(f"{side} Leg Up")
    lean = math.degrees(math.atan2(abs(shoulder[0] - hip[0]), hip[1] - shoulder[1]))
    shoulder_span = math.dist(points[5][:2], points[6][:2])
    forward_bend = (visible(13, 14) and shoulder_span > 5
                    and torso < shoulder_span * 0.65
                    and min(points[13][1], points[14][1]) > hip[1] + shoulder_span * 0.6)
    if lean > 50 or forward_bend:
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
    if not labels and orientation == "Front" and visible(0, 1, 2, *range(5, 17)):
        shoulder_width = abs(points[5][0] - points[6][0])

        def downward(start, end, minimum, slope):
            vertical = points[end][1] - points[start][1]
            return vertical >= torso * minimum and abs(points[end][0] - points[start][0]) <= vertical * slope

        facing = (shoulder_width >= torso * 0.35
                  and abs(points[1][0] - points[2][0]) >= torso * 0.08
                  and points[0][1] < shoulder[1] - torso * 0.1)
        upright = lean <= 15 and abs(points[5][1] - points[6][1]) <= torso * 0.15
        arms_down = all(
            downward(joint, elbow, 0.15, 0.4) and downward(elbow, wrist, 0.15, 0.4)
            and abs(points[wrist][0] - points[joint][0]) <= torso * 0.3
            and points[wrist][1] >= hip[1] - torso * 0.2
            for joint, elbow, wrist in ((5, 7, 9), (6, 8, 10))
        )
        legs_straight = all(
            downward(joint, knee, 0.25, 0.3) and downward(knee, ankle, 0.25, 0.3)
            for joint, knee, ankle in ((11, 13, 15), (12, 14, 16))
        )
        feet_close = (abs(points[15][0] - points[16][0]) <= shoulder_width * 1.1
                      and abs(points[15][1] - points[16][1]) <= torso * 0.15)
        if facing and upright and arms_down and legs_straight and feet_close:
            labels.add("Stand Normal")
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
    parser.add_argument("--config", type=Path, help="Load command-line settings from a JSON file")
    parser.add_argument("--no-intro", action="store_true", help="Skip the startup intro video")
    parser.add_argument("--start-seconds", type=float, default=None, help="Override the session gameplay marker; use 0 to replay from the beginning")
    parser.add_argument("video", type=Path, nargs="?", help="Input MP4 or other OpenCV-readable video")
    parser.add_argument("--ssh-camera", metavar="USER@HOST", help="Receive a remote USB webcam over SSH")
    parser.add_argument("--camera-device", default="/dev/video2")
    parser.add_argument("--camera-width", type=int, default=1280)
    parser.add_argument("--camera-height", type=int, default=720)
    parser.add_argument("--camera-fps", type=int, default=30)
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
    parser.add_argument("--script", type=Path, default=Path(__file__).with_name("script.txt"), help="Spoken gesture script")
    parser.add_argument("--no-script", action="store_true", help="Disable speech and expected-gesture checking")
    parser.add_argument("--tts", choices=("gtts", "neural", "system"), default="gtts", help="gTTS (default) and neural use online services; system is offline")
    parser.add_argument("--voice", default="en-US-AriaNeural", help="Neural TTS voice, e.g. en-US-GuyNeural")
    parser.add_argument("--show", action="store_true", help="Display preview; press q to stop")
    parser.add_argument("--experimental-turns", action="store_true", help="Enable approximate front-to-side turn events")
    parser.add_argument("--max-frames", type=int, default=0, help="Stop after this many frames; 0 processes all")
    return parser


def parse_arguments(parser, argv=None):
    argv = sys.argv[1:] if argv is None else argv
    bootstrap = argparse.ArgumentParser(add_help=False)
    bootstrap.add_argument("--config", type=Path)
    config_path = bootstrap.parse_known_args(argv)[0].config
    if config_path is not None:
        try:
            settings = json.loads(config_path.read_text())
        except (OSError, ValueError) as error:
            parser.error(f"Cannot load config {config_path}: {error}")
        if not isinstance(settings, dict):
            parser.error("Config must be a JSON object")
        actions = {action.dest: action for action in parser._actions if action.dest not in ("help", "config")}
        tokens = []
        seen = set()
        for key, value in settings.items():
            name = key.replace("-", "_")
            if name == "intro":
                if not isinstance(value, str) or value.lower() not in ("yes", "no"):
                    parser.error('Config option intro must be "yes" or "no"')
                name = "no_intro"
                value = value.lower() == "no"
            if name not in actions or name in seen:
                parser.error(f"Unknown or duplicate config option: {key}")
            seen.add(name)
            action = actions[name]
            if isinstance(action, argparse._StoreTrueAction):
                if not isinstance(value, bool):
                    parser.error(f"Config option {key} must be true or false")
                if value:
                    tokens.append(action.option_strings[0])
            else:
                if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                    parser.error(f"Config option {key} must be a string or number")
                if action.option_strings:
                    tokens.append(f"{action.option_strings[0]}={value}")
                else:
                    tokens.append(str(value))
        configured = parser.parse_args(tokens)
        parser.set_defaults(**vars(configured))
    args = parser.parse_args(argv)
    if args.output is not None:
        args.output = Path(str(args.output).replace("{timestamp}", datetime.now().strftime("%Y%m%d-%H%M%S")))
    return args


def play_intro(player):
    intro = Path(__file__).parent / "intro" / "1.mp4"
    if not intro.is_file():
        raise RuntimeError(f"Intro video not found: {intro}; use --no-intro to skip")
    if shutil.which("ffplay") is None:
        raise RuntimeError("Intro playback requires ffplay; use --no-intro to skip")
    logging.getLogger("gesture_detection").info("Playing intro: %s", intro)
    player.show_failures(None, {}, intro_clip=intro)


def video_start_seconds(video, override=None):
    import json
    marker = video.with_suffix(".session.json")
    if override is not None:
        start = override
    elif marker.is_file():
        metadata = json.loads(marker.read_text(encoding="utf-8"))
        start = metadata["gameplay_start_seconds"]
    else:
        start = 0
    if isinstance(start, bool) or not isinstance(start, (int, float)) or not math.isfinite(start) or start < 0:
        raise ValueError("Video start time must be finite and nonnegative")
    return start


def gameplay_cues(cues):
    from gesture_script import gesture_name, is_machee_says
    for index, cue in enumerate(cues):
        if cue.kind == "speech" and gesture_name(cue.value) is not None:
            if index > 0 and cues[index - 1].kind == "read" and is_machee_says(cues[index - 1].value):
                index -= 1
            return cues[index:]
    return cues


def load_script(path, no_intro=False):
    from gesture_script import parse_script
    cues = parse_script(path.read_text(encoding="utf-8"))
    if no_intro:
        cues = [cue for cue in cues if not (cue.kind == "load" and cue.value in ("Intro Image", "Intro Video"))]
    return cues


def main():
    parser = build_parser()
    args = parse_arguments(parser)
    live = args.ssh_camera is not None
    if live == (args.video is not None):
        parser.error("Provide either a video file or --ssh-camera USER@HOST")
    if live and args.start_seconds is not None:
        parser.error("start-seconds is only supported for video input")
    start_seconds = 0 if live else video_start_seconds(args.video, args.start_seconds)
    if min(args.camera_width, args.camera_height, args.camera_fps) <= 0:
        parser.error("Camera dimensions and FPS must be positive")
    if not live and not args.video.is_file():
        parser.error(f"Video does not exist: {args.video}")
    if args.hold <= 0 or args.release < 0 or args.imgsz <= 0 or args.max_frames < 0:
        parser.error("hold/imgsz must be positive; release/max-frames must be nonnegative")
    if not all(0 < threshold <= 1 for threshold in (args.confidence, args.keypoint_confidence)):
        parser.error("Confidence thresholds must be in (0, 1]")
    output = args.output
    if output is not None and not args.no_script and args.tts == "system":
        parser.error("Recording spoken audio requires --tts gtts (default) or neural; system speech cannot be captured")
    show = live or args.show or output is None
    if output is not None and output.suffix.lower() != ".mp4":
        parser.error("Output must have an .mp4 extension")
    csv_path = output.with_suffix(".csv") if output is not None else None
    if output is not None and not live and args.video.resolve() in (output.resolve(), csv_path.resolve()):
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
    if live:
        from live_capture import SSHCamera
        capture = SSHCamera(args.ssh_camera, args.camera_device, args.camera_width, args.camera_height, args.camera_fps)
    else:
        capture = cv2.VideoCapture(str(args.video))
    writer = None
    player = None
    script = None
    audio_recorder = None
    audio_merged = False
    timed_recording = live or (output is not None and (show or not args.no_script))
    frame_index = 0
    processed_frames = 0
    capture_generation = 0
    last_live_timestamp = None
    try:
        if not capture.isOpened():
            raise RuntimeError(f"Cannot decode {args.video}")
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps <= 0:
            raise RuntimeError("Video FPS is invalid; transcode to a constant-frame-rate MP4 first")
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if start_seconds:
            if not capture.set(cv2.CAP_PROP_POS_MSEC, start_seconds * 1000):
                raise RuntimeError("Could not seek to the gameplay start time")
            frame_index = int(capture.get(cv2.CAP_PROP_POS_FRAMES))
            if frame_index >= capture.get(cv2.CAP_PROP_FRAME_COUNT):
                raise ValueError("Gameplay start time is beyond the end of the video")
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            if timed_recording:
                from live_capture import LiveVideoWriter
                writer = LiveVideoWriter(output, width, height, round(fps))
            else:
                writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
                if not writer.isOpened():
                    raise RuntimeError("Could not open MP4 encoder")
        cues = None
        if not args.no_script:
            from gesture_script import ScriptRunner, parse_script
            cues = load_script(args.script, no_intro=args.no_intro)
            if start_seconds:
                cues = gameplay_cues(cues)
        if show:
            from playback import create_player
            player = create_player(fps, int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),
                                   seeking=not live and output is None and args.no_script, live=live)
            if output is not None:
                from session_audio import SessionAudio
                audio_recorder = SessionAudio(output)
                player.start_recording(writer, audio_recorder, width, height, fps)
            if not args.no_intro and not start_seconds and not any(cue.kind == "load" and cue.value == "Intro Video" for cue in (cues or [])):
                play_intro(player)
                if player.closed:
                    return
        if not args.no_script:
            from gesture_script import ScriptRunner, parse_script
            if not show:
                raise ValueError("Spoken scripts require display playback; add --show or use --no-script")
            script = ScriptRunner(cues, paused=lambda: player.paused,
                                  tts=args.tts, voice=args.voice, audio_recorder=audio_recorder, failure_screen=True)
            player.timeline.setToolTip("Seeking is disabled during a spoken script; use --no-script for free playback")
        polygon = np.array(args.roi, dtype=np.int32) if args.roi else None
        states = {}
        seen = {}
        with (csv_path.open("w", newline="") if csv_path is not None else nullcontext()) as csv_file:
            log = csv.writer(csv_file) if csv_file is not None else None
            if log is not None:
                log.writerow(["frame", "seconds", "track_id", "gestures", "orientation_hint", "near_vehicle", "x1", "y1", "x2", "y2"])
            while not args.max_frames or processed_frames < args.max_frames:
                if player is not None:
                    presentation = script.take_video_request() if script is not None else None
                    if presentation is not None:
                        try:
                            if presentation == "show scores":
                                player.show_scores(script.scores())
                            elif presentation == "play congrats":
                                player.show_scores(script.scores())
                                player.show_failures(None, {}, congrats=True)
                            else:
                                play_intro(player)
                        finally:
                            if player.closed:
                                script.stop_event.set()
                            script.video_done.set()
                    failure = script.take_failure_request() if script is not None else None
                    if failure is not None:
                        try:
                            player.show_failures(*failure)
                        finally:
                            script.failure_done.set()
                    action = player.next_action()
                    if action is None:
                        break
                    if action >= 0:
                        if not capture.set(cv2.CAP_PROP_POS_FRAMES, action):
                            player.error.setText("Video seek failed")
                            continue
                        frame_index = int(capture.get(cv2.CAP_PROP_POS_FRAMES))
                        states.clear()
                        seen.clear()
                        for tracker in getattr(model.predictor, "trackers", []):
                            tracker.reset()
                success, frame = capture.read()
                if not success:
                    if live:
                        if capture.error:
                            raise RuntimeError(capture.error)
                        player.clock.setText(capture.status)
                        continue
                    if player is not None and output is None and processed_frames > 0:
                        player.paused = True
                        player.ended = True
                        player.update_play_button()
                        continue
                    break
                if not live and start_seconds and capture.get(cv2.CAP_PROP_POS_MSEC) < start_seconds * 1000:
                    frame_index += 1
                    continue
                timestamp = capture.timestamp if live else frame_index / fps
                recording_timestamp = capture.started + timestamp if live else time.monotonic()
                if audio_recorder is not None and audio_recorder.started is None:
                    audio_recorder.started = recording_timestamp
                if live:
                    if capture.generation != capture_generation or (last_live_timestamp is not None and timestamp - last_live_timestamp > 1):
                        states.clear()
                        seen.clear()
                        for tracker in getattr(model.predictor, "trackers", []):
                            tracker.reset()
                        if script is not None:
                            with script.lock:
                                script.observations.clear()
                                script.results.clear()
                    capture_generation = capture.generation
                    last_live_timestamp = timestamp
                if script is not None and script.thread.ident is None:
                    script.thread.start()
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
                        if script is not None and track_id is not None:
                            assessment, mismatch = script.assess(track_id, active, points, args.keypoint_confidence,
                                                                 box=box, timestamp=timestamp, frame=frame)
                            if assessment:
                                label = assessment
                                text = f"ID {track_id} | {assessment}"
                            if mismatch:
                                color = (0, 0, 255)
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
                if writer is not None and player is None:
                    if timed_recording:
                        writer.write(canvas, recording_timestamp)
                    else:
                        writer.write(canvas)
                if player is not None:
                    if script is not None:
                        player.script_status.setText("Scores" if player.score_entries is not None else script.status())
                        player.set_gesture(script.gesture_image())
                        player.script_status.show()
                    from gesture_script import GESTURES
                    player.gameplay_visible = script is None or script.gesture_image() in GESTURES
                    player.display(canvas, frame_index)
                    if live:
                        player.clock.setText(f"Live | {timestamp:.1f} s")
                frame_index += 1
                processed_frames += 1
                if frame_index % 100 == 0:
                    print(f"Processed {frame_index} frames ({frame_index / fps:.1f}s of video)", flush=True)
        if processed_frames == 0:
            raise RuntimeError("No video frames decoded")
    finally:
        if script is not None:
            script.close()
        capture.release()
        if player is not None:
            player.stop_recording()
        if writer is not None:
            writer.release()
        if player is not None:
            player.close()
        if audio_recorder is not None and writer is not None and player.recording_frames:
            try:
                if script is not None and script.thread.is_alive():
                    raise RuntimeError("Speech worker did not stop; cannot finalize audio safely")
                audio_merged = audio_recorder.merge(output)
            except Exception:
                logging.getLogger("gesture_detection").exception("Audio merge failed; original silent recording preserved")
    if player is not None and player.recording_error is not None:
        raise RuntimeError(f"Session recording failed: {player.recording_error}")
    if output is not None:
        saved_frames = player.recording_frames if player is not None else frame_index
        print(f"Saved {saved_frames} frames: {output}\nLabels: {csv_path}\nAudio: {'application audio included' if audio_merged else 'none'}.")
    else:
        print(f"Displayed {processed_frames} frames. No output files saved.")


if __name__ == "__main__":
    from run_log import run_logged
    raise SystemExit(run_logged(main))