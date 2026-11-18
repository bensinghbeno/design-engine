"""RS00 private CAN protocol over the official AT-framed USB serial adapter."""

import argparse
from datetime import datetime, timezone
import logging
import math
from pathlib import Path
import struct
import time

LOGGER = logging.getLogger("robstride00")


def configure_logging(args):
    directory = Path(__file__).resolve().parent / "logs"
    directory.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    path = directory / f"{stamp}-{args.command}.log"
    for handler in LOGGER.handlers[:]:
        handler.close()
        LOGGER.removeHandler(handler)
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.propagate = False
    formatter = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s")
    formatter.converter = time.gmtime
    for target in (path, directory / "latest.log"):
        handler = logging.FileHandler(target, mode="w", encoding="utf-8")
        handler.setFormatter(formatter)
        LOGGER.addHandler(handler)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(console)
    LOGGER.info("Log: %s", path)
    LOGGER.info("Settings: %s", vars(args))


def packet(kind, motor_id, host_id, data):
    if len(data) != 8:
        raise ValueError("Expected eight CAN data bytes")
    can_id = (kind << 24) | (host_id << 8) | motor_id
    return b"AT" + struct.pack(">I", (can_id << 3) | 4) + b"\x08" + data + b"\r\n"


class Link:
    def __init__(self, port, motor_id, host_id, timeout=0.4):
        self.port = port
        self.motor_id = motor_id
        self.host_id = host_id
        self.timeout = timeout
        self.buffer = bytearray()

    def send(self, kind, data=bytes(8), address_data=None):
        LOGGER.debug("TX kind=%d motor=%d data=%s", kind, self.motor_id, data.hex())
        self.port.reset_input_buffer()
        self.buffer.clear()
        self.port.write(packet(kind, self.motor_id,
                               self.host_id if address_data is None else address_data, data))
        self.port.flush()

    def command_torque(self, torque_nm):
        torque_nm = bounded(torque_nm, -8, 8)
        encoded = int((torque_nm + 14) * 65535 / 28)
        LOGGER.debug("TORQUE command_Nm=%.4f", torque_nm)
        self.send(1, struct.pack(">HHHH", 32767, 32767, 0, 0), address_data=encoded)

    def receive(self, deadline):
        while time.monotonic() < deadline:
            self.buffer.extend(self.port.read(max(1, self.port.in_waiting)))
            while len(self.buffer) >= 2:
                if self.buffer[:2] != b"AT":
                    del self.buffer[0]
                    continue
                if len(self.buffer) < 7:
                    break
                length = self.buffer[6]
                if length > 8:
                    del self.buffer[0]
                    continue
                total = 9 + length
                if len(self.buffer) < total:
                    break
                if self.buffer[total - 2:total] != b"\r\n":
                    del self.buffer[0]
                    continue
                address = int.from_bytes(self.buffer[2:6], "big")
                data = bytes(self.buffer[7:7 + length])
                del self.buffer[:total]
                if address & 7 != 4 or length != 8:
                    continue
                can_id = address >> 3
                if can_id & 255 != self.host_id or (can_id >> 8) & 255 != self.motor_id:
                    continue
                kind = can_id >> 24
                LOGGER.debug("RX kind=%d id=0x%08x data=%s", kind, can_id, data.hex())
                if kind == 21 and int.from_bytes(data[:4], "little"):
                    raise RuntimeError("Motor reported a fault")
                if kind == 2 and (can_id >> 16) & 63:
                    raise RuntimeError("Motor feedback contains fault flags")
                return kind, can_id, data
        raise TimeoutError("No matching motor response; check ID, wiring, switches and bus settings")

    def read(self, index, form="f"):
        self.send(17, struct.pack("<H", index) + bytes(6))
        deadline = time.monotonic() + self.timeout
        while True:
            kind, can_id, data = self.receive(deadline)
            if kind == 17 and data[:2] == struct.pack("<H", index):
                if (can_id >> 16) & 255:
                    raise RuntimeError(f"Register 0x{index:04x} read rejected")
                value = struct.unpack_from("<" + form, data, 4)[0]
                LOGGER.debug("READ register=0x%04x value=%s", index, value)
                return value

    def write(self, index, value, form="f"):
        LOGGER.debug("WRITE register=0x%04x value=%s", index, value)
        encoded = struct.pack("<" + form, value).ljust(4, b"\x00")
        self.send(18, struct.pack("<H", index) + bytes(2) + encoded)

    def checked_write(self, index, value, form="f"):
        self.write(index, value, form)
        actual = self.read(index, form)
        if not math.isclose(actual, value, rel_tol=1e-5, abs_tol=1e-6):
            raise RuntimeError(f"Register 0x{index:04x}: wrote {value}, read {actual}")

    def feedback(self):
        deadline = time.monotonic() + self.timeout
        while True:
            kind, can_id, data = self.receive(deadline)
            if kind == 2:
                position, velocity, torque, temperature = struct.unpack(">HHHH", data)
                self.last_feedback = (
                    position / 65535 * (8 * math.pi) - 4 * math.pi,
                    velocity / 65535 * 66 - 33, temperature / 10,
                )
                LOGGER.debug(
                    "FEEDBACK state=%d position_rad=%.4f speed_rad_s=%.4f "
                    "estimated_torque_Nm=%.4f temperature_C=%.1f",
                    (can_id >> 22) & 3,
                    position / 65535 * (8 * math.pi) - 4 * math.pi,
                    velocity / 65535 * 66 - 33,
                    torque / 65535 * 28 - 14, temperature / 10,
                )
                return (can_id >> 22) & 3

    def stop(self):
        self.send(4)
        if self.feedback() != 0:
            raise RuntimeError("Motor did not confirm disabled state")
        LOGGER.info("Motor confirmed disabled.")


def detect(link):
    mode = link.read(0x7005, "B")
    voltage = link.read(0x701C)
    position = link.read(0x7019)
    velocity = link.read(0x701B)
    if not all(math.isfinite(value) for value in (voltage, position, velocity)):
        raise RuntimeError("Invalid telemetry")
        LOGGER.info(f"Motor ID {link.motor_id}: mode={mode}, bus={voltage:.2f} V, "
          f"position={position:.3f} rad, velocity={velocity:.3f} rad/s")
        LOGGER.info("Protocol response detected; this does not prove the motor model is RS00.")
    return voltage


def rotate(link, speed, seconds, current, acceleration):
    voltage = detect(link)
    if not 24 <= voltage <= 60:
        raise RuntimeError("Bus voltage outside published RS00 range")
    try:
        link.stop()
        link.checked_write(0x7005, 2, "B")
        link.checked_write(0x700A, 0.0)
        link.checked_write(0x7018, current)
        link.checked_write(0x7022, acceleration)
        link.checked_write(0x7028, 10000, "I")
        link.checked_write(0x700A, speed)
        link.send(3)
        if link.feedback() != 2:
            raise RuntimeError("Motor did not confirm enabled state")
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            link.write(0x700A, speed)
            if link.feedback() != 2:
                raise RuntimeError("Motor left running state")
            time.sleep(0.05)
        link.write(0x700A, 0.0)
        deadline = time.monotonic() + abs(speed) / acceleration + 1.0
        while time.monotonic() < deadline:
            velocity = link.read(0x701B)
            if not math.isfinite(velocity):
                raise RuntimeError("Invalid velocity feedback")
            if abs(velocity) < 0.03:
                break
            time.sleep(0.05)
    finally:
        try:
            link.stop()
        except Exception as error:
            LOGGER.error("STOP NOT CONFIRMED: %s. Use the hardware power disconnect.", error)
            raise


def torque_target(angle_deg, torque_nm, max_travel):
    if angle_deg is None:
        return None
    target = math.radians(angle_deg)
    if not math.isfinite(target) or not 0 < abs(target) < max_travel:
        raise ValueError("--angle-deg must be nonzero and inside --max-travel (radians)")
    if target * torque_nm <= 0:
        raise ValueError("--angle-deg and --torque-nm must have the same nonzero sign")
    return target


def timed_torque(link, torque_nm, seconds, max_speed=1.0, max_travel=0.35, angle_deg=None):
    torque_nm = bounded(torque_nm, -8, 8)
    seconds = bounded(seconds, 0.1, 2)
    max_speed = bounded(max_speed, 0.1, 1)
    max_travel = bounded(max_travel, 0.01, 0.5)
    target = torque_target(angle_deg, torque_nm, max_travel)
    try:
        link.stop()
        if not 24 <= detect(link) <= 60:
            raise RuntimeError("Bus voltage outside published RS00 range")
        link.checked_write(0x7005, 0, "B")
        link.checked_write(0x7028, 10000, "I")
        link.command_torque(0)
        if link.feedback() != 0:
            raise RuntimeError("Motor must be disabled before torque setup")
        origin, velocity, temperature = link.last_feedback
        if not all(math.isfinite(value) for value in (origin, velocity, temperature)):
            raise RuntimeError("Invalid torque-test telemetry")
        if abs(velocity) > 0.03 or temperature >= 60:
            raise RuntimeError("Torque test requires stationary motor below 60 C")
        LOGGER.info("Initial angle: %.3f deg; relative target: %s deg", math.degrees(origin), angle_deg)
        link.send(3)
        deadline = time.monotonic() + seconds
        while True:
            if link.feedback() != 2:
                raise RuntimeError("Motor did not confirm running state")
            position, velocity, temperature = link.last_feedback
            if not all(math.isfinite(value) for value in (position, velocity, temperature)):
                raise RuntimeError("Invalid torque-test telemetry")
            travel = (position - origin + 4 * math.pi) % (8 * math.pi) - 4 * math.pi
            if abs(velocity) >= max_speed or abs(travel) >= max_travel or temperature >= 60:
                raise RuntimeError("Torque test speed, travel or temperature trip")
            if target is not None and (travel >= target if target > 0 else travel <= target):
                LOGGER.info("Angle target crossed: relative %.3f deg; disabling", math.degrees(travel))
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                if target is not None:
                    raise TimeoutError("Angle target not reached before timeout")
                break
            link.command_torque(torque_nm)
            time.sleep(min(0.02, remaining))
    finally:
        try:
            link.stop()
        except Exception as error:
            LOGGER.error("STOP NOT CONFIRMED: %s. Use the hardware power disconnect.", error)
            raise


def bounded(value, minimum, maximum):
    number = float(value)
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise argparse.ArgumentTypeError(f"Expected {minimum} through {maximum}")
    return number


def identifier(value):
    number = int(value, 0)
    if not 0 <= number <= 253:
        raise argparse.ArgumentTypeError("Use a unicast ID from 0 to 253")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["ports", "detect", "rotate", "torque", "stop"])
    parser.add_argument("--port", help="Prefer /dev/serial/by-id/... on Linux")
    parser.add_argument("--motor-id", type=identifier)
    parser.add_argument("--host-id", type=identifier, default=253)
    parser.add_argument("--baud", type=int, default=921600)
    parser.add_argument("--speed", type=lambda value: bounded(value, -1.0, 1.0), default=0.2,
                        help="Target velocity in rad/s: -1 to 1 (default: 0.2)")
    parser.add_argument("--seconds", type=lambda value: bounded(value, 0.1, 20), default=2.0,
                        help="Rotation duration: 0.1-20 seconds (default: 2)")
    parser.add_argument("--current", type=lambda value: bounded(value, 0.1, 8), default=0.5,
                        help="Motor current limit in A (default: 0.5; maximum: 8; not a continuous rating)")
    parser.add_argument("--acceleration", type=lambda value: bounded(value, 0.1, 1), default=0.5)
    parser.add_argument("--torque-nm", type=lambda value: bounded(value, -8, 8),
                        help="MIT torque command in Nm; only for torque mode (maximum magnitude 8)")
    parser.add_argument("--max-speed", type=lambda value: bounded(value, 0.1, 1), default=1.0,
                        help="Torque-mode software speed trip in rad/s, not speed regulation (default: 1)")
    parser.add_argument("--max-travel", type=lambda value: bounded(value, 0.01, 0.5), default=0.35,
                        help="Torque-mode software displacement trip in rad (default: 0.35)")
    parser.add_argument("--angle-deg", type=float,
                        help="Torque mode: signed relative angle in degrees; disables at crossing, no hold")
    confirmation = parser.add_mutually_exclusive_group()
    confirmation.add_argument("--confirm-unloaded-rs00", action="store_true")
    confirmation.add_argument("--confirm-secured-load-rs00", action="store_true",
                              help="Confirm bolted RS00, guarded load and mechanical fall protection")
    args = parser.parse_args()
    if args.command != "ports" and (not args.port or args.motor_id is None):
        parser.error("--port and --motor-id are required; no automatic scanning or motion")
    if args.motor_id == args.host_id:
        parser.error("Motor and host IDs must differ")
    if args.command == "rotate":
        if not (args.confirm_unloaded_rs00 or args.confirm_secured_load_rs00):
            parser.error("Confirm either an unloaded RS00 or a secured load with mechanical fall protection")
        if args.current > 1 and not args.confirm_secured_load_rs00:
            parser.error("Above 1 A requires --confirm-secured-load-rs00")
    if args.command == "torque":
        if args.torque_nm is None or not args.confirm_secured_load_rs00:
            parser.error("torque requires --torque-nm and --confirm-secured-load-rs00")
        if args.seconds > 2:
            parser.error("Torque tests are capped at 2 seconds")
        try:
            torque_target(args.angle_deg, args.torque_nm, args.max_travel)
        except ValueError as error:
            parser.error(str(error))
    elif args.torque_nm is not None:
        parser.error("--torque-nm requires the torque command")
    if args.angle_deg is not None and args.command != "torque":
        parser.error("--angle-deg requires the torque command")
    configure_logging(args)
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        LOGGER.error("Missing pyserial dependency")
        parser.exit(1, "Install dependency: python -m pip install -r robstride00/requirements.txt\n")
    if args.command == "ports":
        for device in list_ports.comports():
            LOGGER.info(f"{device.device}: {device.description} [{device.hwid}]")
        LOGGER.info("Port listing completed; no motor connection opened.")
        return
    try:
        with serial.Serial(args.port, args.baud, timeout=0.02, write_timeout=0.2,
                           exclusive=True) as port:
            port.reset_input_buffer()
            link = Link(port, args.motor_id, args.host_id)
            if args.command == "detect":
                detect(link)
            elif args.command == "stop":
                link.stop()
            elif args.command == "torque":
                timed_torque(link, args.torque_nm, args.seconds, args.max_speed, args.max_travel,
                             args.angle_deg)
            else:
                rotate(link, args.speed, args.seconds, args.current, args.acceleration)
            LOGGER.info("Command completed successfully.")
    except (OSError, RuntimeError, TimeoutError, KeyboardInterrupt) as error:
        LOGGER.exception("Command failed or interrupted: %s", error)
        parser.exit(1, f"Stopped: {error}\n")


if __name__ == "__main__":
    main()