"""Parse spoken prompts and run their response windows off the UI thread."""

import re
import logging
import hashlib
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path


GESTURES = {
    "Left Hand Up", "Right Hand Up", "Both Hands Up", "Left Leg Up",
    "Right Leg Up", "Bend Down", "Turn Left", "Turn Right", "Turn Back", "Stand Normal",
}
SUPPORTED = GESTURES - {"Turn Left", "Turn Right", "Turn Back"}


@dataclass(frozen=True)
class Cue:
    kind: str
    value: str | float


def parse_script(text):
    cues = []
    if text.count("[") != text.count("]"):
        raise ValueError("Unbalanced brackets in gesture script")
    for token in re.split(r"(\[[^\[\]]*\])", text):
        if token.startswith("["):
            directive = token[1:-1].strip()
            delay = re.fullmatch(r"delay\s+(\d+(?:\.\d+)?)\s*(?:sec|seconds?|s)", directive, re.IGNORECASE)
            if delay:
                cues.append(Cue("delay", float(delay.group(1))))
            elif directive.lower().startswith("delay"):
                raise ValueError(f"Invalid delay: [{directive}]")
            else:
                cues.append(Cue("visual", directive))
        else:
            if "[" in token or "]" in token:
                raise ValueError("Malformed brackets in gesture script")
            for line in token.splitlines():
                if line.strip():
                    cues.append(Cue("speech", line.strip()))
    return cues


def required_visible(expected, points, threshold):
    joints = {
        "Left Hand Up": (5, 6, 7, 9, 11, 12),
        "Right Hand Up": (5, 6, 8, 10, 11, 12),
        "Both Hands Up": (5, 6, 7, 8, 9, 10, 11, 12),
        "Left Leg Up": (5, 6, 11, 12, 13, 15, 16),
        "Right Leg Up": (5, 6, 11, 12, 14, 15, 16),
        "Bend Down": (5, 6, 11, 12),
        "Stand Normal": (0, 1, 2, *range(5, 17)),
    }
    return expected in joints and all(points[index][2] >= threshold for index in joints[expected])


class ScriptRunner:
    def __init__(self, cues, paused=lambda: False, speaker=None, tts="neural", voice="en-US-AriaNeural"):
        self.cues = cues
        self.paused = paused
        self.speaker = speaker or self.speak
        self.tts = tts
        self.voice = voice
        executable = "ffplay" if tts == "neural" else "spd-say"
        if speaker is None and shutil.which(executable) is None:
            raise RuntimeError(f"Speech requires {executable}, or use --no-script")
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, name="gesture-speech", daemon=True)
        self.expected = None
        self.phase = "Starting"
        self.caption = ""
        self.observations = {}
        self.results = {}
        self.error = None
        self.process = None
        self.feedback_pending = []
        self.feedback_sent = set()

    def queue_feedback(self, outcome):
        if outcome not in self.feedback_sent:
            logging.getLogger("gesture_detection").info("Gesture feedback: %s; expected=%s", outcome, self.expected)
            self.feedback_sent.add(outcome)
            self.feedback_pending.append(outcome)

    def play_feedback(self, outcome):
        frequencies = (880, 1175) if outcome == "success" else (330, 220)
        tone = (f"sine=frequency={frequencies[0]}:duration=0.16[first];"
                f"sine=frequency={frequencies[1]}:duration=0.22[second];"
                "[first][second]concat=n=2:v=0:a=1,volume=0.5")
        self.run_audio_command(["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", "-f", "lavfi", tone])
        if outcome == "wrong" and not self.stop_event.is_set():
            self.speaker("Wrong gesture detected")

    def drain_feedback(self):
        while not self.stop_event.is_set() and not self.paused():
            with self.lock:
                if not self.feedback_pending:
                    return
                outcome = self.feedback_pending.pop(0)
            self.play_feedback(outcome)

    def speak(self, text):
        if self.tts == "system":
            self.run_audio_command(["spd-say", "--wait", "--priority", "message", "--", text])
            return
        cache = Path.home() / ".cache" / "gesture-detection" / "speech"
        cache.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(f"{self.voice}\n{text}".encode()).hexdigest()
        audio = cache / f"{key}.mp3"
        if not audio.exists():
            with tempfile.TemporaryDirectory(dir=cache) as temporary:
                destination = Path(temporary) / "speech.mp3"
                self.run_audio_command([
                    sys.executable, "-m", "edge_tts", "--voice", self.voice,
                    "--text", text, "--write-media", str(destination),
                ])
                if self.stop_event.is_set():
                    return
                if not destination.exists() or destination.stat().st_size == 0:
                    raise RuntimeError("Neural TTS returned no audio; check your internet connection")
                destination.replace(audio)
        if not self.stop_event.is_set():
            self.run_audio_command(["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", str(audio)])

    def run_audio_command(self, command):
        with tempfile.TemporaryFile() as errors, subprocess.Popen(command,
                              stdout=subprocess.DEVNULL, stderr=errors) as process:
            self.process = process
            started = time.monotonic()
            while process.poll() is None:
                if self.stop_event.wait(.05) or time.monotonic() - started > 120:
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    if not self.stop_event.is_set():
                        raise RuntimeError("Speech service timed out")
                    return
            if process.returncode:
                errors.seek(0)
                detail = errors.read().decode(errors="replace").strip()
                raise RuntimeError(detail[-1000:] or "Speech service failed")
            self.process = None

    def wait(self, seconds):
        remaining = seconds
        previous = time.monotonic()
        while not self.stop_event.wait(.02):
            self.drain_feedback()
            current = time.monotonic()
            if not self.paused():
                remaining -= current - previous
            previous = current
            if remaining <= 0:
                return

    def run(self):
        try:
            for cue in self.cues:
                if self.stop_event.is_set():
                    return
                while self.paused() and not self.stop_event.wait(.05):
                    pass
                if self.stop_event.is_set():
                    return
                if cue.kind == "speech":
                    logging.getLogger("gesture_detection").info("Speaking prompt: %s", cue.value)
                    with self.lock:
                        self.expected = cue.value if cue.value in GESTURES else None
                        self.phase = "Speaking"
                        self.caption = str(cue.value)
                        self.observations.clear()
                        self.results.clear()
                        self.feedback_pending.clear()
                        self.feedback_sent.clear()
                    self.speaker(str(cue.value))
                    with self.lock:
                        self.phase = "Respond"
                elif cue.kind == "visual":
                    with self.lock:
                        self.caption = str(cue.value)
                else:
                    logging.getLogger("gesture_detection").info("Response delay: %s seconds", cue.value)
                    self.wait(float(cue.value))
                    with self.lock:
                        if self.expected:
                            self.phase = "Result"
                            self.results = {
                                track_id: "Matched" if matched else "Not performed" if visible else "Cannot verify"
                                for track_id, (matched, visible) in self.observations.items()
                            }
                            logging.getLogger("gesture_detection").info("Gesture results: expected=%s tracks=%s", self.expected, self.results)
                            if "Not performed" in self.results.values():
                                self.queue_feedback("wrong")
                    if self.expected:
                        self.wait(1.0)
                        self.drain_feedback()
            with self.lock:
                self.phase = "Finished"
        except Exception as error:
            logging.getLogger("gesture_detection").exception("Speech worker failed")
            with self.lock:
                self.error = str(error)
                self.phase = "Speech error"

    def assess(self, track_id, labels, points, threshold):
        with self.lock:
            expected = self.expected
            if not expected or self.phase not in ("Respond", "Result"):
                return "", False
            if expected not in SUPPORTED:
                return f"Cannot verify: {expected} unsupported", False
            if self.phase == "Result":
                status = self.results.get(track_id, "Cannot verify")
                return f"{status} | Expected: {expected}", status == "Not performed"
            visible = required_visible(expected, points, threshold)
            matched, observed = self.observations.get(track_id, (False, False))
            matched = matched or expected in labels
            self.observations[track_id] = (matched, observed or visible)
            if matched:
                self.queue_feedback("success")
                return f"Matched: {expected}", False
            if not visible:
                return f"Cannot verify | Expected: {expected}", False
            if labels:
                self.queue_feedback("wrong")
                return f"Wrong gesture: {', '.join(sorted(labels))} | Expected: {expected}", True
            return f"Waiting for: {expected}", False

    def status(self):
        with self.lock:
            return f"{self.phase}: {self.error or self.caption}"

    def close(self):
        self.stop_event.set()
        if self.thread.ident is not None:
            self.thread.join(timeout=3)