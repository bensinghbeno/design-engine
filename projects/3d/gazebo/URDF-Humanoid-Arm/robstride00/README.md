# RobStride 00 Bench Setup

- [Wiring SVG](robstride-00.svg): proposed detection-test wiring.
- [Wiring YAML](robstride-00.yaml): signal connections and first-rotation checklist; documentation, not executable configuration.

## Hardware and Connections

The photographed motor is a RobStride 00 rated at 48 V DC. The published supply range is 24-60 V; verify the supply against the motor revision before use. USB powers only the RobStride CH340/GD32 USB-C CAN adapter (SKU 100012096), not the motor.

With the board's component side facing you, green terminal at the top and USB at the bottom, the terminals are **GND | CANH | CANL**, left to right. Follow the PCB labels; the underside view is mirrored.

| Motor connection | Destination | Status |
| --- | --- | --- |
| CAN-H | Debugger CANH | Confirmed signal connection |
| CAN-L | Debugger CANL | Confirmed signal connection |
| Thin red | Proposed CANH | Harness color mapping unverified |
| Thin black | Proposed CANL | Harness color mapping unverified |
| VBAT+ (likely thick red) | Fused external supply positive | Verify cable polarity |
| Motor GND (likely thick black) | External supply negative | Verify cable polarity |

The official manual's socket diagram shows VBAT+ and GND as the large contacts, with CAN-L above CAN-H at the right when oriented as illustrated. Trace the unplugged harness with a continuity meter to identify its wires. The mating cable face is mirrored. Debugger ground wiring remains unresolved; do not connect a thin CAN wire to GND or assume isolation.

The Seeed B601-RS guide specifies red to H and black to L for its **splitter-board cable**, not this direct motor harness. Its pictured USB-A adapter and PCAN setup differ from this USB-C serial adapter.

## Switches and Communication

- Switch 1 **OFF**: normal operation. ON enters bootloader mode.
- Switch 2 **ON**: adds a 120-ohm termination resistor at the adapter end; do not duplicate existing endpoint termination.
- Standard CAN wiring uses two 120-ohm end resistors, approximately 60 ohms in parallel with power disconnected.
- Official RS00 CAN 2.0 manual: 1 Mbps CAN bus; confirm actual firmware/settings.
- Official USB-CAN adapter: AT framing, header `41 54`, trailer `0D 0A`. The adapter datasheet specifies a maximum serial baud of 921600, not proof of its current setting. Serial baud and CAN bitrate are separate.

## Detection Before Motion

1. Secure the unloaded motor and keep the shaft clear. Disconnect motor power and USB before wiring.
2. Verify power polarity and that both thin wires are CAN. Connect the proposed pair only after those checks.
3. Reconnect and use device detection/read status only. Do not enable motion during wire identification.
4. If detection fails, disconnect motor power and USB before swapping only the thin CAN pair. Never swap power polarity.
5. Failed detection may also mean incorrect serial/CAN settings, motor ID, switches, ground reference or termination.

For first rotation, use compatible official software, confirm fault-free feedback, set conservative current/torque and acceleration limits, select velocity mode with zero target, then enable. An example slow target is 0.2 output rad/s (about 1.9 rpm), only after verifying units. Stop with zero target, wait for rest, then disable. Keep a hardware power disconnect accessible.

## Software Findings

Use [official MotorStudio releases](https://github.com/RobStride/MotorStudio/releases); a [Linux AppImage release](https://github.com/RobStride/MotorStudio/releases/tag/v1%2C0%2C1) is available. Verify RS00 compatibility before enabling. Native Linux does not require the video's Windows/WSL USBIPD steps.

The pinned K-Scale revision `021d360a20803934a8db23e770857bc7bd4f500b` accepts only motor types 01-04, not 00. Its WASD example expects two motors, requests zeroing, and never sets nonzero control gains. The supervisor starts/enables automatically. Do not run it unchanged or substitute another motor type. The video description itself warns that it is outdated and targets RS04.

Motor detection and velocity-mode rotation have been exercised on the connected RS00; see the user-confirmed loaded test below. Watchdog fault-response behavior has not been independently verified.

## Python CLI

Run these commands from the workspace root in your chosen Python environment:

```bash
python -m pip install -r robstride00/requirements.txt
python robstride00/control.py ports
python robstride00/control.py detect --port /dev/ttyUSB0 --motor-id 1
```

Replace the port and motor ID with the actual values. Detection reads mode, bus voltage, position and velocity; it does not enable, zero or configure the motor. It verifies a protocol response, not model identity. The serial default is 921600 (`--baud` overrides it). This tool assumes the official adapter is already in AT mode with its CAN bus matching the motor, typically 1 Mbps. It does not configure the adapter or switch motor protocols. Close MotorStudio before using the serial port.

Only after successful detection, confirmed RS00 identity, secure unloaded mounting and correct wiring:

```bash
python robstride00/control.py rotate --port /dev/ttyUSB0 --motor-id 1 --speed 0.2 --seconds 2 --confirm-unloaded-rs00
python robstride00/control.py stop --port /dev/ttyUSB0 --motor-id 1
```

Use `--speed -0.2` for the opposite direction. Rotation is capped at 1.0 rad/s in either direction and 20 seconds. Set duration with `--seconds` (0.1-20, default 2). Default current limit is 0.5 A (`--current`, maximum 8 A); default acceleration is 0.5 rad/s^2 (`--acceleration`, maximum 1). These are test limits, not certified safe limits for an attached mechanism. Supply current limiting is separate.

For any loaded test, replace `--confirm-unloaded-rs00` with `--confirm-secured-load-rs00`, confirming a bolted motor, guarded fixture and mechanical protection against the load falling when the motor disables. Above 1 A this flag is mandatory. Start with short tests and increase the current limit incrementally, not directly to 8 A. The local RS00 manual lists 4.7 Apk rated-load phase current and 15.5 Apk maximum-load phase current. The 8 A software ceiling is not a continuous rating or verification that a five-second test is thermally safe, and amperes are not a torque command in Nm. This flag does not add a brake, load monitoring or temperature monitoring; the controller still disables on completion or failure.

Every rotation repeats the full setup: disable, select velocity mode, zero the speed target, set current limit and acceleration, configure the watchdog, and set the requested speed before enabling. All parameter writes in this setup are verified by read-back. It requires watchdog register `0x7028` to read back 10000 ticks (0.5 seconds per the referenced manual) before enabling. Unsupported firmware causes an abort; do not bypass this check. It refreshes speed commands while expecting fault-free feedback, commands zero speed after the requested duration, waits for deceleration, and disables in a `finally` block, including on Ctrl+C. Duration excludes setup and final deceleration. Settings are not explicitly saved to flash or restored afterward. Do not rely solely on software stopping or watchdog read-back: keep the hardware disconnect accessible. A killed process, unplugged cable or power failure prevents software confirmation of stopping.

For the detected motor at ID 127, close MotorStudio's serial connection first. With a secured load and mechanical fall protection, run from the workspace root:

```bash
.venv/bin/python robstride00/control.py rotate \
	--port /dev/ttyUSB0 --motor-id 127 \
	--speed 0.1 --current 0.5 --acceleration 0.5 --seconds 2 \
	--confirm-secured-load-rs00
```

These arguments are respectively rad/s, A, rad/s^2, and seconds. Use `--confirm-unloaded-rs00` instead for a securely mounted unloaded motor. Repeat the command for another run; no manual parameter reset is needed. The target-before-enable sequence is covered by offline tests and the user-confirmed run below.

### User-Confirmed Loaded Velocity Test

The user reported this command working for the discussed 2 kg load at a 20 cm lever arm. Run from the workspace root, after closing MotorStudio's serial connection:

```bash
.venv/bin/python robstride00/control.py rotate --port /dev/ttyUSB0 --motor-id 127 --speed 1.0 --current 8.0 --acceleration 0.5 --seconds 3 --confirm-secured-load-rs00
```

| Argument | Meaning |
| --- | --- |
| `--speed 1.0` | Target output velocity, 1 rad/s (about 9.55 rpm) |
| `--current 8.0` | Maximum motor current allowance, not a constant draw or an 8 Nm command |
| `--acceleration 0.5` | Velocity ramp, 0.5 rad/s^2; GUI calls this Speed Step |
| `--seconds 3` | Command interval including acceleration; setup and final deceleration are additional |

Velocity mode adjusts torque to follow the speed target within its limits. A successful lift is not verification of continuous or repeated thermal safety at 8 A. Keep the load guarded, allow sufficient travel, and provide mechanical fall protection: the script disables after deceleration and does not hold the load. This is a recorded working configuration, not the recommended initial test setting.

The CLI never automatically clears faults, zeroes the encoder, scans IDs, updates firmware or changes CAN bitrate. If detection fails, check port permissions, actual ID, serial baud, bus bitrate, switches and wiring. Disconnect motor power and USB before rewiring.

Offline validation:

```bash
python -m unittest discover -s robstride00 -p 'test_control.py' -v
```

The loaded velocity test above is user-confirmed. Watchdog operation under communication loss remains unverified on hardware.

## Timed or Angle-Limited MIT Torque

`torque` is separate from velocity-mode `rotate`: it commands Nm with KP/KD zero, not amperes. `--speed`, `--current`, and `--acceleration` apply to `rotate`, not this torque command. There is no velocity regulation or position hold in this mode.

Close MotorStudio's serial connection. With a guarded fixture and mechanical fall protection, first verify direction and stopping using a low-torque test:

```bash
.venv/bin/python robstride00/control.py torque --port /dev/ttyUSB0 --motor-id 127 --torque-nm 0.2 --angle-deg 10 --seconds 1 --confirm-secured-load-rs00
```

`--angle-deg 10` means 10 degrees from the angle measured at startup, not an absolute encoder angle. Negative travel requires both negative angle and negative torque. The target must be nonzero and inside `--max-travel` (default 0.35 radians, approximately 20 degrees). Omitting `--angle-deg` gives a timed torque test instead. Torque magnitude is capped at 8 Nm; duration is 0.1-2 seconds. A timeout before reaching the requested angle is reported as an error, followed by a Stop attempt.

The controller verifies mode 0 and the watchdog, stages zero torque, and checks that the motor is stationary and below 60 C before enabling. It trips on reported speed at `--max-speed` (default and maximum 1 rad/s), displacement at `--max-travel` (maximum 0.5 rad), or reported temperature at 60 C. At target crossing, timeout, trip, or Ctrl+C, it attempts Stop and requires disabled feedback. Serial latency and the 0.4-second receive timeout can delay stopping. These sampled trips are not guaranteed physical limits; overshoot and coasting are possible. The temperature trip and two-second cap do not establish thermal safety at 8 Nm.

**Disabling releases torque and can drop a suspended load.** A rated mechanical catch and hardware cutoff are required; do not use the motor as the sole load support. Angle-limited torque does not brake to or hold an exact position. This functionality has offline tests only; verify it physically at low torque before increasing incrementally.

## Run Logs

Every valid command automatically writes `logs/<UTC timestamp>-<command>.log` and replaces `logs/latest.log`, relative to this folder, regardless of the working directory. The log path is printed at startup. No extra argument is needed; use one controller process at a time.

Logs include settings, transmitted commands, register read-backs, raw replies, returned position/speed/estimated torque/temperature, confirmed disables, and errors or Ctrl+C tracebacks. Feedback is decoded from existing RS00 type-2 responses; logging adds no CAN requests. The current value in settings is the commanded limit, not measured motor current. Torque feedback is a motor estimate, not a load-cell measurement. Logging does not add temperature, stall or travel protection. Argument-validation failures occur before log creation.

After a test, ask to check the latest log. Logs are flushed per record, but a killed process or power failure may leave no final stop result. Archive logs accumulate; remove old ones as needed. Generated logs are ignored by Git.

## Sources

- [Official RS00 manual, sections 2.2 and 3.1](https://raw.githubusercontent.com/RobStride/Product_Information/main/Product%20Literature/CAN2.0/RS00/RS00User%20Manual260713.pdf)
- [USB-CAN adapter datasheet](https://www.mouser.com/datasheet/3/1361/1/100012096.pdf)
- [Seeed B601-RS wiring guide](https://wiki.seeedstudio.com/rebot_b601_rs_getting_started/)
- [Pinned K-Scale WASD example](https://github.com/kscalelabs/actuator/blob/021d360a20803934a8db23e770857bc7bd4f500b/examples/wasd_control.py)
- [Video and description](https://www.youtube.com/watch?v=-IVK60lWsBg)