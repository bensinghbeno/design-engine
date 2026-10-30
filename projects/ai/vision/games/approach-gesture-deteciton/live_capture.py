"""Latest-frame USB camera capture through an authenticated SSH pipe."""

import re
import logging
import shlex
import subprocess
import tempfile
import threading
import time
from fractions import Fraction


class LiveVideoWriter:
    def __init__(self, path, width, height, fps):
        import av
        self.container = av.open(str(path), mode="w")
        self.stream = self.container.add_stream("mpeg4", rate=fps)
        self.stream.width = width
        self.stream.height = height
        self.stream.pix_fmt = "yuv420p"
        self.stream.bit_rate = 6000000
        self.stream.time_base = Fraction(1, 1000)
        self.stream.codec_context.time_base = Fraction(1, 1000)
        self.start = None
        self.last_pts = -1

    def write(self, image, timestamp):
        import av
        if self.start is None:
            self.start = timestamp
        frame = av.VideoFrame.from_ndarray(image, format="bgr24")
        frame.pts = max(self.last_pts + 1, round((timestamp - self.start) * 1000))
        frame.time_base = Fraction(1, 1000)
        self.last_pts = frame.pts
        for packet in self.stream.encode(frame):
            self.container.mux(packet)

    def release(self):
        try:
            for packet in self.stream.encode():
                self.container.mux(packet)
        finally:
            self.container.close()


def camera_command(host, device, width, height, fps):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+@[A-Za-z0-9][A-Za-z0-9_.-]*", host):
        raise ValueError("SSH host must be user@hostname or user@IPv4-address")
    if not re.fullmatch(r"/dev/video\d+", device):
        raise ValueError("Camera device must be /dev/videoN")
    remote = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
              "-f", "v4l2", "-input_format", "mjpeg", "-framerate", str(fps),
              "-video_size", f"{width}x{height}", "-i", device,
              "-an", "-c:v", "copy", "-f", "image2pipe", "pipe:1"]
    return ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
            "-o", "ServerAliveInterval=3", "-o", "ServerAliveCountMax=2",
            host, shlex.join(remote)]


class SSHCamera:
    def __init__(self, host, device="/dev/video2", width=1280, height=720, fps=30):
        self.command = camera_command(host, device, width, height, fps)
        self.width, self.height, self.fps = width, height, fps
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.latest = None
        self.process = None
        self.error = None
        self.status = "Connecting to remote webcam"
        self.started = time.monotonic()
        self.last_received = self.started
        self.timestamp = 0.0
        self.generation = 0
        self.thread = threading.Thread(target=self.receive, name="ssh-camera", daemon=True)
        self.thread.start()

    def receive(self):
        try:
            import av
            for attempt in range(3):
                if self.stop.is_set():
                    return
                logging.getLogger("gesture_detection").info("SSH camera connection attempt %s/3", attempt + 1)
                with tempfile.TemporaryFile() as errors:
                    try:
                        process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=errors)
                        with self.lock:
                            self.process = process
                            self.last_received = time.monotonic()
                            self.latest = None
                            self.status = f"Connecting (attempt {attempt + 1}/3)"
                        with av.open(process.stdout, format="mjpeg", options={"probesize": "32768", "analyzeduration": "0"}) as container:
                            for decoded in container.decode(video=0):
                                if self.stop.is_set():
                                    return
                                frame = decoded.to_ndarray(format="bgr24")
                                now = time.monotonic()
                                with self.lock:
                                    if self.status != "Live":
                                        logging.getLogger("gesture_detection").info("Camera streaming: %sx%s", frame.shape[1], frame.shape[0])
                                    self.latest = (frame, now - self.started, attempt)
                                    self.last_received = now
                                    self.status = "Live"
                    except Exception as error:
                        if not self.stop.is_set():
                            logging.getLogger("gesture_detection").exception("Camera stream interrupted")
                        self.status = f"Reconnecting: {error}"
                    finally:
                        process = self.process
                        if process is not None:
                            process.terminate() if process.poll() is None else None
                            try:
                                process.wait(timeout=2)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                process.wait()
                            if process.stdout is not None:
                                process.stdout.close()
                        with self.lock:
                            self.process = None
                            self.latest = None
                    errors.seek(0)
                    detail = errors.read().decode(errors="replace").strip()
                    if detail:
                        logging.getLogger("gesture_detection").warning("Remote camera stderr: %s", detail)
                if self.stop.wait(1):
                    return
            self.error = f"Remote camera disconnected after three attempts. {detail or self.status}"
        except Exception as error:
            logging.getLogger("gesture_detection").exception("Camera worker failed")
            self.error = str(error)

    def isOpened(self):
        return not self.stop.is_set()

    def get(self, property_id):
        import cv2
        return {cv2.CAP_PROP_FPS: self.fps, cv2.CAP_PROP_FRAME_WIDTH: self.width,
                cv2.CAP_PROP_FRAME_HEIGHT: self.height, cv2.CAP_PROP_FRAME_COUNT: 0}.get(property_id, 0)

    def read(self):
        with self.lock:
            if self.latest is not None:
                frame, self.timestamp, self.generation = self.latest
                self.latest = None
                return True, frame
            if time.monotonic() - self.last_received > 12 and self.process is not None:
                if self.process.poll() is None:
                    self.process.terminate()
        return False, None

    def release(self):
        self.stop.set()
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()
        self.thread.join(timeout=5)