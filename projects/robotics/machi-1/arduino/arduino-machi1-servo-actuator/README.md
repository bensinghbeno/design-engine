# Servo Actuator

Target: classic Arduino Uno/Nano (ATmega328P). Servo signal: D9; RUN: D6;
direction: D7. Buttons connect to ground. AS5600 wiring remains 3.3 V, GND,
SDA and SCL. Use an external servo-rated power supply with common ground.

## Buttons And Potentiometer

Connect a 10 kohm linear potentiometer's outer terminals to Arduino 5V and
GND, and its center wiper to A0. Do not connect it to the external servo supply.
Swap the outer terminals to reverse knob direction. Do not leave A0 floating.
See [wiring diagram](actuator_angle_control.svg) and its
[YAML source](actuator_angle_control.yaml).

With `potentiometerMode = true` and `manualTestMode = false`, startup commands
center (135 nominal degrees / 1500 us), without calibration or EEPROM access.
Keep the mechanism clear: resetting or opening a serial monitor can cause a
large initial move. AS5600 is used only for logging; a missing sensor does not
disable controls. Existing EEPROM contents are left untouched.

Release D6 and wait for `BUTTONS ARMED` (at least one second after startup).
Center is held until you press D6 or move the potentiometer. Hold D6 to move;
D7 selects direction at each run start (released increases, pressed decreases).
Buttons override the pot. Releasing D6 holds position until you move the pot
by at least 8 ADC counts from its release reading. Pot changes while D6 is held
do not take over. Z/z slews to center; D6 cancels centering. Move the pot again
after centering to take over.

A0 readings up to 115 (including 110..115) command zero (500 us).
Readings 115..1023 map to 0..250 nominal degrees (500..2352 us).
Eight readings are averaged every 20 ms; a 6 us deadband reduces jitter,
except at zero so the command reaches exactly 500 us. Movement is limited
to 4 us per update.
Set `potentiometerMode = false` for buttons only. Numeric serial angle commands
are available only in manual test mode. This is open-loop position control;
the one-second startup delay does not confirm physical settling.

## Manual Test (Optional)

Setting `manualTestMode = true` disables buttons and potentiometer control.
Startup commands 135 nominal degrees
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
The same upper pulse limit applies to button and potentiometer motion. Start
near center; do not test extremes until their mechanical safety is confirmed.
Leave several seconds between commands so the log captures settling.

`COMMAND` lines record the requested angle and pulse. `SAMPLE` lines every
250 ms record uptime, commanded pulse, nominal angle and independent AS5600
angle. These are not calibrated feedback targets. Startup logs capture the
initial move as well. Inputs received during the two-second startup are ignored.

`POT` lines record raw A0, averaged ADC, requested and commanded pulses,
readiness, attachment and control modes. `pot_active=1` indicates pot ownership;
`average=-1` means no control sample yet. Button events log D6/D7 and direction.

Ctrl+C stops recording but does not disable the servo; it may keep holding its
last command. Logs are saved as `logs/manual-servo-*.log` inside this folder.
Share the log filename for later analysis.

## Build

```sh
arduino-cli compile --fqbn arduino:avr:uno arduino/arduino-machi1-servo-actuator
```