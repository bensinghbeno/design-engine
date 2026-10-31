"""Reconstruct application playback on the recording clock and mux it into MP4."""

import logging
import json
import signal
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path


class SessionAudio:
    def __init__(self, video=None):
        if shutil.which("ffmpeg") is None:
            raise RuntimeError("Recording speech requires ffmpeg")
        self.started = None
        self.events = []
        self.journal = Path(video).with_suffix(".audio.json") if video is not None else None

    def record(self, command, started, ended):
        if self.started is not None:
            source = ["-f", "lavfi", "-i", command[-1]] if "lavfi" in command else ["-i", command[-1]]
            self.events.append((max(0, started - self.started), max(0, ended - started), source))
            if self.journal is not None:
                temporary = self.journal.with_suffix(".json.tmp")
                temporary.write_text(json.dumps(self.events), encoding="utf-8")
                temporary.replace(self.journal)

    def merge(self, video):
        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            return self._merge(video)
        finally:
            signal.signal(signal.SIGINT, previous)

    def _merge(self, video):
        if not self.events:
            return False
        logger = logging.getLogger("gesture_detection")
        video = Path(video)
        logger.info("Merging %s audio playback events into %s", len(self.events), video)
        print("Finalizing audio; please wait. Ctrl+C is disabled until the merge finishes.", flush=True)
        with tempfile.TemporaryDirectory(dir=video.parent) as directory:
            audio_path = Path(directory) / "session.wav"
            merged = Path(directory) / "merged.mp4"
            sample_rate = 24000
            cursor = 0
            with wave.open(str(audio_path), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(sample_rate)
                for offset, duration, source in self.events:
                    target = round(offset * sample_rate)
                    silence = max(0, target - cursor)
                    while silence:
                        count = min(silence, sample_rate)
                        audio.writeframesraw(b"\0\0" * count)
                        silence -= count
                        cursor += count
                    raw = Path(directory) / "clip.pcm"
                    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", *source,
                                    "-t", str(duration), "-ac", "1", "-ar", str(sample_rate),
                                    "-f", "s16le", str(raw)], check=True, capture_output=True, timeout=120)
                    with raw.open("rb") as clip:
                        clip.seek(max(0, cursor - target) * 2)
                        while block := clip.read(sample_rate * 2):
                            audio.writeframesraw(block)
                            cursor += len(block) // 2
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(video),
                            "-i", str(audio_path), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                            "-c:a", "aac", "-af", "apad", "-shortest", "-movflags", "+faststart", str(merged)],
                           check=True, capture_output=True, timeout=300)
            merged.replace(video)
        logger.info("Audio merge completed: %s", video)
        return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Retry audio merging using a saved session timeline")
    parser.add_argument("video", type=Path)
    arguments = parser.parse_args()
    recorder = SessionAudio(arguments.video)
    recorder.events = json.loads(recorder.journal.read_text(encoding="utf-8"))
    if recorder.merge(arguments.video):
        print(f"Audio merge completed: {arguments.video}")