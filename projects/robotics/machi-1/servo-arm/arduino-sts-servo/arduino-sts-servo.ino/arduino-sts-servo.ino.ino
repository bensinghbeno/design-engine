#include <SCServo.h>

SMS_STS servo;

constexpr uint8_t servoId = 1;
constexpr long servoBaud = 1000000;
constexpr int16_t clockwiseSpeed = 300;
constexpr uint8_t acceleration = 10;
constexpr uint8_t directionPin = 8;
constexpr uint8_t runPin = 9;
constexpr unsigned long debounceMs = 30;
constexpr unsigned long reversalPauseMs = 500;

struct Button {
  uint8_t pin;
  bool lastReading = HIGH;
  bool stableState = HIGH;
  unsigned long changedAt = 0;

  Button(uint8_t buttonPin) : pin(buttonPin) {}

  bool pressed(unsigned long now) {
    bool reading = digitalRead(pin);
    if (reading != lastReading) {
      lastReading = reading;
      changedAt = now;
    }
    if (reading != stableState && now - changedAt >= debounceMs) {
      stableState = reading;
      return stableState == LOW;
    }
    return false;
  }
};

Button directionButton = {directionPin};
Button runButton = {runPin};
bool running = false;
bool clockwise = true;
bool reversing = false;
unsigned long reversalStartedAt = 0;
int16_t commandedSpeed = 0;

void setup() {
  pinMode(directionPin, INPUT_PULLUP);
  pinMode(runPin, INPUT_PULLUP);
  directionButton.lastReading = directionButton.stableState = digitalRead(directionPin);
  runButton.lastReading = runButton.stableState = digitalRead(runPin);
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
  unsigned long now = millis();
  bool directionPressed = directionButton.pressed(now);
  runButton.pressed(now);
  running = runButton.stableState == LOW;

  if (directionPressed) {
    clockwise = !clockwise;
    if (running) {
      reversing = true;
      reversalStartedAt = now;
    }
  }
  if (!running) {
    reversing = false;
  }
  if (reversing && now - reversalStartedAt >= reversalPauseMs) {
    reversing = false;
  }

  int16_t targetSpeed = running && !reversing
                            ? (clockwise ? clockwiseSpeed : -clockwiseSpeed)
                            : 0;
  if (targetSpeed != commandedSpeed) {
    servo.WriteSpe(servoId, targetSpeed, acceleration);
    commandedSpeed = targetSpeed;
  }
}
