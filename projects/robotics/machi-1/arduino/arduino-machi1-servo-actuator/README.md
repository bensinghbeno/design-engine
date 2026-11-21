# Servo Actuator

Target: classic Arduino Uno/Nano (ATmega328P). Servo signal: D9; RUN: D6;
direction: D7. Buttons connect to ground. AS5600 wiring remains 3.3 V, GND,
SDA and SCL. Use an external servo-rated power supply with common ground.

## Automatic Mode (Currently Enabled)

`manualTestMode = false`: calibration is loaded from EEPROM or measured and
saved before buttons are enabled. Each measurement needs a full second with
at most 0.5 degrees peak-to-peak variation, within a 10-second timeout. Sensor
errors still abort immediately. The 0..250 degree command limit remains active.

Run the launcher below to flash and record button tests. Wait for `BUTTONS ARMED`,
then hold D6 to move and release to hold. D7 selects direction at each run start.
Numeric serial angle commands are available only in manual mode; Z/z centers
in automatic mode.

Hardware verification: calibration and EEPROM read-back passed; reset reused
the saved mapping with no calibration sweep. Physical button movement and
off-center restart still require testing.

## Manual Test (Optional)

Setting `manualTestMode = true` bypasses calibration and buttons without reading or
writing EEPROM. After sensor detection, startup commands 135 nominal degrees
(1500 us), logs for two seconds, then accepts serial commands. This delay does
not certify physical stability. Keep the mechanism clear before starting.

From the repository root, compile, flash and open a recorded serial session:

```sh
bash arduino/arduino-machi1-servo-actuator/test-servo.sh
```

An optional first argument selects the port (default `/dev/ttyUSB0`). Close
other serial monitors first. The default board is `arduino:avr:uno`; set `FQBN`
only if your board requires another target.

Wait for `READY`, then type an angle such as `135`, `130`, or `140` and press
Enter. Commands accept 0..250 nominal degrees, mapped to 500..2352 us. The
original 270-degree / 2000-us scale is retained; the range is capped, not rescaled.
The same upper pulse limit applies to button motion and calibrated startup. Start
near center; do not test extremes until their mechanical safety is confirmed.
Leave several seconds between commands so the log captures settling.

`COMMAND` lines record the requested angle and pulse. `SAMPLE` lines every
250 ms record uptime, commanded pulse, nominal angle and independent AS5600
angle. These are not calibrated feedback targets. Startup logs capture the
initial move as well. Inputs received during the two-second startup are ignored.

Ctrl+C stops recording but does not disable the servo; it may keep holding its
last command. Logs are saved as `logs/manual-servo-*.log` inside this folder.
Share the log filename for later analysis.

## Startup Calibration (Manual Mode Disabled)

Set `manualTestMode = false` to restore the following behavior.

- After AS5600 detection, the sketch checks the EEPROM record at address 0.
- With no valid record, it commands 1500 us, then measures 1400, 1600 and
  1500 us. Keep the mechanism clear: the first command can cause a large move.
  Buttons are disabled throughout calibration.
- Calibration checks magnet status, stable readings, center consistency and
  a plausible response for the nominal 270-degree servo. A versioned record
  with a CRC is written only after successful measurement and read back.
- With a valid record, the current AS5600 angle is converted to a pulse before
  the first servo signal. No center sweep is repeated. Out-of-range angles or
  invalid readings leave the servo signal off and button control disabled.
- After success, release D6 and wait one second to arm. Hold D6 to move;
  D7 selects direction at the start of each run. Z/z still commands center.

The mapping assumes the sensor measures the servo output directly, less than
one revolution of travel, and an approximately linear pulse-to-angle response.
A short calibration estimates the full range; backlash, load and nonlinearity
can still cause movement on reset. It is not continuous closed-loop control.
Sensor angle is logged separately from nominal commanded position.

Calibration failures require inspection and reset. Signal-off does not guarantee
load holding or electrical power removal. Do not rely on this as an emergency stop.
Recalibrate after changing the servo or magnet alignment: invalidate the reserved
EEPROM record (its first four bytes) before resetting. This triggers the same
automatic center test. Uploading a sketch does not normally erase EEPROM.

## Build

```sh
arduino-cli compile --fqbn arduino:avr:uno arduino/arduino-machi1-servo-actuator
```