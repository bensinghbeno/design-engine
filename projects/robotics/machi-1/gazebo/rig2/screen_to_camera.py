#!/usr/bin/env python3
"""Stream an X11 desktop to a v4l2loopback camera using FFmpeg (video only).

System setup on Ubuntu/Debian, run manually:
    sudo apt install ffmpeg x11-utils v4l2loopback-dkms
    sudo modprobe v4l2loopback video_nr=10 card_label=ScreenCamera exclusive_caps=1

Start from a terminal in an X11 desktop session:
    python3 screen_to_camera.py --device /dev/video10 --fps 30

In OBS, add a Video Capture Device (V4L2) source and select ScreenCamera
after starting this script. Avoid displaying the OBS preview on the captured
screen to prevent video feedback. Audio is not captured.

Wayland is not supported: use OBS Screen Capture (PipeWire), or log into an
Xorg session. This script never loads kernel modules or requests root access.
"""

import argparse
import fcntl
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import struct
import subprocess
import sys


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Must be greater than zero.")
    return number


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--device", type=Path, default=Path("/dev/video10"))
    parser.add_argument("--display", default=os.environ.get("DISPLAY"),
                        help="X11 display (default: DISPLAY environment variable)")
    parser.add_argument("--width", type=positive_int, default=1280,
                        help="Output width (default: 1280)")
    parser.add_argument("--height", type=positive_int, default=720,
                        help="Output height (default: 720)")
    parser.add_argument("--fps", type=positive_int, default=30)
    parser.add_argument("--hide-cursor", action="store_true")
    return parser


def check_device(device: Path) -> None:
    if not device.exists():
        raise RuntimeError(
            f"{device} does not exist. Create a v4l2loopback device first; see --help."
        )
    if not stat.S_ISCHR(device.stat().st_mode):
        raise RuntimeError(f"{device} is not a camera character device.")
    try:
        descriptor = os.open(device, os.O_RDWR | os.O_NONBLOCK)
    except PermissionError as exc:
        raise RuntimeError(
            f"No read/write permission for {device}. Ask an administrator to add "
            "your user to the video group, then log out and back in."
        ) from exc
    try:
        capability = bytearray(104)
        fcntl.ioctl(descriptor, 0x80685600, capability, True)
        driver = capability[:16].split(b"\0", 1)[0]
        if driver not in (b"v4l2 loopback", b"v4l2loopback"):
            raise RuntimeError(f"Refusing to write to {device}: not a v4l2loopback device.")
        capabilities, device_caps = struct.unpack_from("=II", capability, 84)
        effective_caps = device_caps if capabilities & 0x80000000 else capabilities
        if not effective_caps & 0x2:
            raise RuntimeError(
                f"{device} has no video output capability. Stop any other camera "
                "producer; if it persists, ask an administrator to reload v4l2loopback."
            )
    finally:
        os.close(descriptor)


def get_screen_size(display: str) -> str:
    if not shutil.which("xdpyinfo"):
        raise RuntimeError("xdpyinfo is missing. Install the x11-utils package.")
    result = subprocess.run(["xdpyinfo", "-display", display],
                            capture_output=True, text=True, timeout=10,
                            env={**os.environ, "LC_ALL": "C"})
    if result.returncode:
        raise RuntimeError(f"Cannot query X11 display {display}: {result.stderr.strip()}")
    dimensions = re.search(r"^\s*dimensions:\s+([1-9]\d*x[1-9]\d*)\s+pixels",
                           result.stdout, re.MULTILINE)
    if dimensions is None:
        raise RuntimeError(f"Cannot determine the full screen size for {display}.")
    return dimensions.group(1)


def build_command(args: argparse.Namespace) -> list[str]:
    filters = (
        f"scale={args.width}:{args.height}:force_original_aspect_ratio=decrease,"
        f"pad={args.width}:{args.height}:(ow-iw)/2:(oh-ih)/2,"
        "setsar=1,format=yuyv422"
    )
    return [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "warning",
        "-f", "x11grab", "-framerate", str(args.fps),
        "-video_size", get_screen_size(args.display),
        "-draw_mouse", "0" if args.hide_cursor else "1", "-i", args.display,
        "-an", "-vf", filters, "-c:v", "rawvideo", "-pix_fmt", "yuyv422",
        "-threads", "1", "-f", "v4l2", str(args.device),
    ]


def stream(command: list[str]) -> int:
    process = subprocess.Popen(command, start_new_session=True)
    try:
        return process.wait()
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("Linux with X11 and v4l2loopback is required.")
    if os.environ.get("XDG_SESSION_TYPE") == "wayland" or os.environ.get("WAYLAND_DISPLAY"):
        parser.error("Wayland is unsupported. Use OBS Screen Capture (PipeWire) or an Xorg session.")
    if not args.display:
        parser.error("No X11 display. Run from your desktop terminal or pass --display :0.")
    if not re.fullmatch(r"/dev/video\d+", str(args.device)):
        parser.error("Device must be an absolute path such as /dev/video10.")
    if args.width % 2 or args.height % 2:
        parser.error("Width and height must be even.")
    if not shutil.which("ffmpeg"):
        parser.error("FFmpeg is missing. Install it using your system package manager.")
    try:
        check_device(args.device)
        print(f"Capturing display {args.display} -> {args.device} "
              f"({args.width}x{args.height}, {args.fps} fps).", flush=True)
        print("In OBS, add a Video Capture Device (V4L2) source. Ctrl+C stops capture.",
              flush=True)
        if stream(build_command(args)):
            raise RuntimeError("FFmpeg stopped unexpectedly. See its error above.")
    except KeyboardInterrupt:
        print("\nScreen camera stopped.")
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def handle_sigterm(signum: int, frame: object) -> None:
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)
    sys.exit(main())