# Video Gesture Detection

Local YOLO26-Pose inference with ByteTrack IDs, rule-based gestures, and MP4/CSV output.

## Run

```bash
.venv/bin/python detect_gestures.py vehicle-recording-approach.mp4 --skeleton --device 0
.venv/bin/python detect_gestures.py /path/to/video.mp4 --output output/annotated.mp4
```

By default, the annotated video appears in a resizable display window and no MP4 or CSV is saved. Press q or Escape, or close the window, to stop. Use --output to explicitly save an MP4 and matching CSV; add --show to display while saving. Existing outputs are never overwritten. CSV rows contain frame number, video time, tracking ID, gesture labels, an approximate orientation hint, ROI membership, and box coordinates. Multiple compatible gestures can appear together. The output MP4 has no audio. Timing assumes a constant-frame-rate input.

Options:

- `--show`: also display when saving with --output; display is already the default without --output.
- `--max-frames 120`: process a short sample.
- `--imgsz 640`: lower inference resolution for speed (default 960).
- `--device cpu`: run without CUDA.
- `--hold 0.4`: confirmation duration, in video seconds.
- `--keypoint-confidence 0.5`: minimum joint confidence.
- `--roi "100,200;900,200;900,700;100,700"`: polygon around the near-vehicle ground area, using source-video pixel coordinates. Replace these example coordinates with ones appropriate to your camera. Membership uses the midpoint of visible ankles, not physical distance. Hidden ankles produce Unknown. All people are still annotated.
- `--experimental-turns`: approximate front-to-side body turns using face position relative to shoulders. These are not reliable head/body rotation measurements.

## Scope and Limitations

The six static labels from gestures.txt are implemented: Left Hand Up, Right Hand Up, Both Hands Up, Left Leg Up, Right Leg Up, Bend Down. Left/right refers to anatomical side, as estimated by the pose model. Rules use wrists, shoulders, hips, knees, and ankles, not finger gestures. The list is a specification, not text prompts or a trained classifier; adding a line does not create a new detector.

Turn Left and Turn Right are experimental and disabled by default. Turn Back is intentionally unsupported: missing facial landmarks cannot distinguish facing away from occlusion. Reliable turn detection needs labelled examples and a validated temporal orientation/action model. A screen-direction hint is exported separately from gesture labels.

This is a baseline, not a validated suspicious-behavior detector. Normal walking, perspective, crouching and occlusion can cause false labels or missed events. Tune and evaluate on labelled examples from your camera. No listed gesture means no rule fired, not proof of normal behavior. Unknown indicates insufficient visible joints. Tracking IDs may change after occlusion. Gesture rules do not provide calibrated probabilities or infer intent.

Without --roi, proximity is Not configured. There is no automatic vehicle detection. ROI proximity is an image-space approximation; raised legs can affect its ground estimate. Use a calibrated ground-plane method for metric distances.

## Install

Python 3.10 and Linux x86_64 were tested on an RTX A2000 with driver 535.261.03. A CUDA 12.1 PyTorch build is pinned for this driver. The system CUDA toolkit is not required.

```bash
python3.10 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v test_gestures.py
```

YOLO weights download on the first run. Subsequent inference is local. Review Ultralytics licensing before distributing a commercial application.