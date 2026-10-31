# Video Gesture Detection

Local YOLO26-Pose inference with ByteTrack IDs, rule-based gestures, and MP4/CSV output.

## Recording Regression

`validation/session-20261030-194436.mp4` is the reference copied from the session used to diagnose missed Left Leg Up and Bend Down gestures. Run `.venv/bin/python -m unittest -v test_validation.py` to rerun YOLO26s-Pose on it. Local model weights are required; CUDA is used when available, otherwise CPU. This test does not open the remote camera, speak, or overwrite the last-run log.

The test uses actual decoded video timestamps: Left Leg Up at 41.0-43.9 seconds, Bend Down at 80.0-82.6 seconds, and standing negative controls at 39.0-40.7 and 78.0-79.4 seconds. It samples approximately every 0.3 seconds and checks temporal confirmation. The recording contains burned-in annotations, so this is a regression reference, not an independent accuracy benchmark. The existing older video and gestures-valid.txt are preserved; this test does not claim to score the whole gesture script.

## Run

Audio finalization temporarily ignores Ctrl+C; wait for `Audio merge completed`. Each recorded session now saves a matching `.audio.json` playback timeline as clips finish. If merging fails, retry with `.venv/bin/python session_audio.py output/session-NAME.mp4`. Keep the speech cache and timeline for this recovery. Older recordings without a timeline cannot be recovered exactly by this command. Force-killing the program can still prevent finalization.

Record an annotated live-camera session while displaying it and running spoken prompts:

```bash
.venv/bin/python detect_gestures.py --ssh-camera ben@10.0.0.226 --camera-device /dev/video2 --device 0 --skeleton --script gestures.txt --output "output/session-$(date +%Y%m%d-%H%M%S).mp4"
```

Live recordings preserve receive-time spacing between processed frames, including pauses/gaps, instead of speeding up dropped frames. The MP4 contains the annotated video image (boxes, labels and optional skeleton), not window controls or the prompt-status widget. Neural speech and feedback tones are merged as AAC audio when recording ends. A matching CSV records detections. Close the window, press q/Escape, or press Ctrl+C once and wait for finalization; force-killing the process may leave it incomplete. Existing files are not overwritten.

Audio recording uses the exact speech clips and generated tones, aligned to audio-player launch timestamps. Device playback latency may cause a small synchronization offset. Microphone, source-video audio, and other system sounds are not captured. Scripted file recordings also use real playback timing to keep narration aligned. FFmpeg is required; --tts system is not supported with scripted recording. With --no-script or no played audio, recordings remain silent. On merge failure, the original silent video is preserved and the error is logged.

Each command-line invocation overwrites `last_run.log` beside the script. It mirrors Python console output and records the command, timestamps, exit status, Python tracebacks, speech prompts/results, and remote camera errors/reconnections. It is flushed during the run and ignored by Git. Native-library output written directly to OS file descriptors and hard process crashes are not captured by this Python logger. The log may contain script text and hostnames; review it before sharing. Only the latest run is kept, so inspect it before rerunning.

```bash
.venv/bin/python detect_gestures.py vehicle-recording-approach.mp4 --skeleton --device 0
.venv/bin/python detect_gestures.py /path/to/video.mp4 --output output/annotated.mp4
```

By default, the annotated video appears in a resizable display window and no MP4 or CSV is saved. Press q or Escape, or close the window, to stop. Use --output to explicitly save an MP4 and matching CSV; add --show to display while saving a file. Existing outputs are never overwritten. CSV rows contain frame number, video time, tracking ID, gesture labels, an approximate orientation hint, ROI membership, and box coordinates. Multiple compatible gestures can appear together. Source-video timing assumes a constant-frame-rate input.

The file player has a play/pause button, FPS textbox with Apply (or Enter), three-second backward/forward buttons, and a seek bar with elapsed/total seconds. Space toggles playback when the video window has focus outside the textbox. FPS is a target presentation rate (0 < FPS <= 240), limited by inference speed; it does not change source timestamps. Seeking preserves pause state and resets tracking and gesture history. At the end, seek backward or press Play to restart. Seeking is disabled while saving output to preserve sequential export. Source-video audio is not played.

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

## Spoken Prompts

Gesture feedback plays on the speech worker without blocking video inference. A match produces a rising success tone. A detected wrong gesture or missed response deadline produces a falling warning tone followed by "Wrong gesture detected" in the selected voice. Each outcome is played at most once per prompt across all tracked people, so repeated frames cannot spam audio. Correcting a wrong gesture can still produce the success tone. Unknown/occluded poses remain silent. Feedback and narration are serialized; feedback can delay the next prompt. Both TTS backends require ffplay for tones.

The player reads gestures.txt on a background thread by default. Neural speech uses `edge-tts` with Microsoft's online speech service and the `en-US-AriaNeural` voice. Only spoken text is sent, not video. Internet access is required for uncached prompts. Audio is cached under `~/.cache/gesture-detection/speech` and played locally with `ffplay` (required; installed on this machine).

```bash
.venv/bin/python detect_gestures.py vehicle-recording-approach.mp4 --skeleton --voice en-US-AriaNeural
.venv/bin/python detect_gestures.py vehicle-recording-approach.mp4 --skeleton --voice en-US-GuyNeural
```

Use `--tts system` for the older offline Speech Dispatcher voice, or `--no-script` to disable narration and restore free seeking. There is no silent fallback to the system voice if neural synthesis fails; errors appear in the player. A first-time synthesis request may delay a prompt while video continues playing.

`[Read: Perform Action]` speaks "Perform Action" without setting a validation target. `[Read: Perform Action] Left Hand Up` speaks the readout, then the gesture name, then waits a one-second grace period before evaluating Left Hand Up. `[delay 3 sec]` provides the following three-second response window. Other bracketed cues remain display-only visual captions. Exact supported gesture names outside brackets set the expected action. A wrong detected gesture produces a red box; a visible person who misses the following delay deadline gets a red Not performed result for one second. Hidden required joints produce Cannot verify. Results are per tracking ID, and a successful gesture is remembered for its response window.

Delays use wall-clock playback time and freeze while paused; a sentence already playing may finish. Seeking is disabled during scripted tests. Prerecorded video must already align with prompt timing; speech cannot change what the recorded person does. Turn prompts are not supported for compliance checking. Use --no-script for headless export, or --show for a spoken test.

## Detection Limits

`Stand Normal` is also supported: face visible and approximately front-facing, torso upright, both arms hanging nearly vertically with wrists near/below the hips, straight upright legs, and feet no wider than approximately shoulder width. Face, arm, hip, knee and ankle joints must meet the confidence threshold. It uses the same hold duration and spoken-test feedback as other gestures. This is a 2D geometric approximation, not proof of body orientation; validate thresholds for your camera angle. Cropped feet or hidden joints cannot verify this pose.

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