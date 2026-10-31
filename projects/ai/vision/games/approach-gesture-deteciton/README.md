# Video Gesture Detection

Local YOLO26-Pose inference with ByteTrack IDs, rule-based gestures, and MP4/CSV output.

## Recording Regression

`validation/session-20261030-194436.mp4` is the reference copied from the session used to diagnose missed Left Leg Up and Bend Down gestures. Run `.venv/bin/python -m unittest -v test_validation.py` to rerun YOLO26s-Pose on it. Local model weights are required; CUDA is used when available, otherwise CPU. This test does not open the remote camera, speak, or overwrite the last-run log.

The test uses actual decoded video timestamps: Left Leg Up at 41.0-43.9 seconds, Bend Down at 80.0-82.6 seconds, and standing negative controls at 39.0-40.7 and 78.0-79.4 seconds. It samples approximately every 0.3 seconds and checks temporal confirmation. The recording contains burned-in annotations, so this is a regression reference, not an independent accuracy benchmark. The existing older video and gestures-valid.txt are preserved; this test does not claim to score the whole gesture script.

## Run

Load the supplied live-camera settings with:

```bash
.venv/bin/python detect_gestures.py --config config.json
```

JSON config keys match command-line option names (hyphens or underscores, without `--`); use `video` for the positional input. All runtime options are supported, including boolean flags as JSON `true`/`false`. Unknown keys and invalid values are rejected. Explicit CLI values override configured defaults, for example `--config config.json --device cpu --no-intro`. Relative paths use the current working directory, just like CLI paths. `{timestamp}` in `output` expands to local `YYYYMMDD-HHMMSS` at launch; shell expressions are not executed. The supplied config matches the SSH camera command and generates a new timestamped recording name each launch.

Interactive launches always use one fullscreen window. When enabled, `intro/1.mp4` plays inside that window with audio; the model is loaded and camera connection starts beforehand. The last intro frame stays visible until a camera frame replaces it, without closing or replacing the window. Scripted prompts begin afterward. Escape closes the application; use `--no-intro` or config `"intro": "no"` to bypass the intro. Headless exports do not play it.

With `--output` and a display, the session records the rendered application window, including intro video, welcome image, camera/reference layout, labels, controls, and failure-review grids/videos. Speech, feedback, and intro/review clip audio share the recording timeline. The window is fitted without cropping into the configured camera resolution; captures follow UI updates with real elapsed timestamps. This captures application audio only, not microphone or other desktop audio. Headless exports retain camera-only output. CSV frame indices and timestamps still describe camera detections, not presentation frames.

Audio finalization temporarily ignores Ctrl+C; wait for `Audio merge completed`. Each recorded session now saves a matching `.audio.json` playback timeline as clips finish. If merging fails, retry with `.venv/bin/python session_audio.py output/session-NAME.mp4`. Keep the speech cache and timeline for this recovery. Older recordings without a timeline cannot be recovered exactly by this command. Force-killing the program can still prevent finalization.

Record an annotated live-camera session while displaying it and running spoken prompts:

```bash
.venv/bin/python detect_gestures.py --ssh-camera ben@10.0.0.226 --camera-device /dev/video2 --device 0 --skeleton --script script.txt --output "output/session-$(date +%Y%m%d-%H%M%S).mp4"
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

Tamil gesture text is mapped to the existing images and validation rules without changing the spoken text:

| Tamil script text | Gesture |
| --- | --- |
| இடது கையை உயர்த்தவும் | Left Hand Up |
| வலது கையை உயர்த்தவும் | Right Hand Up |
| இரு கைகளையும் உயர்த்தவும் | Both Hands Up |
| இடது காலை மேலே தூக்கு | Left Leg Up |
| வலது காலை மேலே தூக்கு | Right Leg Up |
| சாதாரணமாக நில் | Stand Normal |
| குனியுங்கள் | Bend Down |

Both `[Read: மச்சி சொல்கிறார்]` and `[Read: மாச்சி சொல்கிறார்]` authorize the next gesture like `[Read: Machee Says]`. An unprefixed Tamil gesture retains the previous pose, following the same game rules. Tamil mappings also work for early image previews and replay-start trimming. Use `--tts neural --voice ta-IN-PallaviNeural` for Tamil speech; the default gTTS backend is still configured for English.

Generic partial-image matching handles differently framed duplicate photos: it searches textured image windows at multiple scales in both directions, then requires template correlation of at least 0.65 and more than 50% matching pixels in the aligned window. Low-detail images and substantially different aspect ratios are excluded from this fallback. Higher-scoring entries take priority. This uses OpenCV image matching, not person identification or an Intel model; similar backgrounds or repeated patterns can still produce false matches.

An additional pixel check accepts more than 50% matching pixels after center cropping, resizing to 48x96, smoothing, and limited alignment. A pixel matches within 30 levels per Lab channel; nonoverlapping pixels count as mismatches. Compatible overall color and body-pattern correlation are also required so shared backgrounds alone do not merge participants. The highest-scoring entry remains. Partial crops containing another participant can still fail this check.

Duplicate-photo filtering also compares upper- and lower-clothing hue/saturation distributions to tolerate arm-position changes. Both regions must match; this fallback requires enough color information to avoid treating plain gray clothing as distinctive. As with other appearance matching, participants wearing very similar outfits can still be merged. The highest-scoring entry is retained.

New GUI recordings save a matching `.session.json` file with `gameplay_start_seconds`, measured from the recording's first frame. The marker is written once when the camera gameplay is first presented, after the opening media. Keep this file alongside the MP4: video-input replay automatically seeks to the marker and skips script cues before the first gesture, preserving its preceding `Machee Says` authorization. Use `--start-seconds 0` to override the marker and replay from the beginning, or `--start-seconds 24.802` to specify a start time for an older recording. This only aligns the start; it does not reconstruct later script timing or remove recorded reference panels and review clips.

The scoreboard suppresses duplicate or closely similar participant photos, keeping the entry with the highest percentage (ties use the lowest tracking ID). Photo matching compares color and spatial patterns while tolerating resizing and small lighting changes. This is an appearance heuristic, not verified identity recognition: large pose changes may be missed, and nearly identical appearances may be merged. Missing photos remain separate. This display filtering does not combine or modify recorded scores.

`[Show Scores]` displays participant photos, earned points, and percentages in medal rows: Gold is 90-100%, Silver is 50% to below 90%, and Bronze is below 50%. A verifiable round earns one point only if it finishes Matched with no detected mistake; corrected mistakes earn zero. Cannot verify rounds are excluded from the denominator. Participants with no verifiable rounds appear as Unscored. Scores use tracked participant IDs and retain totals when the existing short-gap reassociation identifies an ID change; long tracking losses can still split a participant into separate IDs. The initial visible participant crop is used as their photo.

`[Play Congrats]` plays a random `congrats/*.mp4` with audio in the right 25% while scores remain in the left 75%. Scores stay visible after playback. The score display and congratulations video/audio are included in session recordings.

`[Load:Intro Video]` plays `intro/1.mp4` in the fullscreen application and waits for completion before the next script cue. When present in an active script, it suppresses automatic startup intro playback to avoid duplication. Config `"intro": "no"` or `--no-intro` skips both `[Load:Intro Video]` and `[Load:Intro Image]`, as well as automatic startup playback. Adjacent readouts, delays, and gameplay cues remain unchanged. Follow it with `[Load:Intro Image][Read:Hello welcome to Machee Says Game!!]` to show the welcome image during narration when intros are enabled. Scripted intro media and its audio are included in displayed session recordings.

`[Load:Intro Image][Read:Hello welcome to Machee Says Game!!]` displays `intro/intro-image.jpeg` across the full viewing area during the adjacent readout. It stays through the following delay; the next gesture prompt restores the camera/reference split. This scripted image works with or without the startup intro video. Load directives are not spoken.

Scripts containing `[Read: Machee Says]` use the Machee Says rule: that readout authorizes the next gesture change. Without it, participants must maintain the last authorized pose (initially Stand Normal), even though the new gesture is spoken. The reference image shows the pose to keep. During these hold rounds, success is decided at the response deadline; a confidently detected different gesture remains a failure even if the participant returns to the correct pose. The existing one-second grace period still applies. Scripts without any Machee Says readout retain ordinary gesture validation.

After a response window with a detected mistake or a final missed gesture, the script waits while the display shows participant crops in a labelled grid on the left (75%) and a randomly selected `bad/*.mp4` clip with audio on the right (25%). The first detected mistake frame is retained even if the participant later corrects the gesture and finishes as Matched. Final misses without a detected wrong gesture use the latest visible response crop. Clean matches and unverifiable participants without recorded mistakes are excluded. Normal playback resumes after the clip; closing the window stops the review. Review crops are held in memory, not saved as separate files. The failure grid, video, and clip audio are included in session recordings. Missing or unreadable clips show an error and allow the script to continue.

Gesture feedback plays on the speech worker without blocking video inference. A match produces a rising success tone. A detected wrong gesture or missed response deadline produces a falling warning tone followed by "Wrong gesture detected" in the selected voice. Each outcome is played at most once per prompt across all tracked people, so repeated frames cannot spam audio. Correcting a wrong gesture can still produce the success tone. Unknown/occluded poses remain silent. Feedback and narration are serialized; feedback can delay the next prompt. Both TTS backends require ffplay for tones.

The player reads script.txt on a background thread by default. Speech defaults to `--tts gtts`, using Google's text-to-speech service with English and normal speed. Use `--tts neural` for the previous Microsoft `edge-tts` voice (`en-US-AriaNeural`); `--voice` applies only to that backend. Only spoken text is sent, not video. Internet access is required for uncached prompts. Audio is cached separately for each voice under `~/.cache/gesture-detection/speech` and played locally with `ffplay` (required; installed on this machine). Both online backends support session audio recording, feedback, and the one-second gesture grace period.

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