#include <SCServo.h>

SMS_STS servo;

constexpr uint8_t servoId = 1;
constexpr long servoBaud = 1000000;
constexpr int16_t clockwiseSpeed = 300;
constexpr uint8_t acceleration = 10;
constexpr unsigned long rotationDurationMs = 3000;
constexpr unsigned long stopDurationMs = 500;

void setup() {
  Serial.begin(servoBaud);
  servo.pSerial = &Serial;
  delay(500);

  if (servo.ReadPos(servoId) < 0) {
    while (true) {
      delay(1000);
    }
  }

  servo.EnableTorque(servoId, 0);
  servo.unLockEprom(servoId);
  servo.WheelMode(servoId);
  servo.LockEprom(servoId);
  servo.WriteSpe(servoId, 0, acceleration);
  servo.EnableTorque(servoId, 1);
}

void loop() {
  servo.WriteSpe(servoId, clockwiseSpeed, acceleration);
  delay(rotationDurationMs);
  servo.WriteSpe(servoId, 0, acceleration);
  delay(stopDurationMs);

  servo.WriteSpe(servoId, -clockwiseSpeed, acceleration);
  delay(rotationDurationMs);
  servo.WriteSpe(servoId, 0, acceleration);
  delay(stopDurationMs);
}
