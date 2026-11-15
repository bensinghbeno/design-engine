#include <Servo.h>

Servo myServo;
const int servoPin = 9;
const int buttonPinDirection = 7;
const int buttonPinRun = 6;
const int minPulseUs = 500;
const int maxPulseUs = 2500;
const int stepPulseUs = 4;
const unsigned long updateIntervalMs = 20;
const unsigned long debounceMs = 30;
const unsigned long startupSettleMs = 1000;

int targetPulseUs = 1500;
int lastRunState = HIGH;
int movementDirection = 1;
bool armed = false;
bool moving = false;
unsigned long startupMs = 0;
unsigned long runChangedMs = 0;
unsigned long lastUpdateMs = 0;

void rotateServo(int direction) {
  targetPulseUs = constrain(targetPulseUs + direction * stepPulseUs,
                            minPulseUs, maxPulseUs);
  myServo.writeMicroseconds(targetPulseUs);
}

void setup() {
  pinMode(buttonPinRun, INPUT_PULLUP);
  pinMode(buttonPinDirection, INPUT_PULLUP);
  myServo.writeMicroseconds(targetPulseUs);
  myServo.attach(servoPin, minPulseUs, maxPulseUs);
  lastRunState = digitalRead(buttonPinRun);
  startupMs = millis();
  runChangedMs = startupMs;
}

void loop() {
  const unsigned long now = millis();
  const int runState = digitalRead(buttonPinRun);
  if (runState != lastRunState) {
    lastRunState = runState;
    runChangedMs = now;
  }

  if (runState == HIGH) {
    moving = false;
    lastUpdateMs = now;
    if (now - startupMs >= startupSettleMs && now - runChangedMs >= debounceMs) {
      armed = true;
    }
    return;
  }

  if (!armed || now - runChangedMs < debounceMs) {
    return;
  }

  if (!moving) {
    movementDirection = digitalRead(buttonPinDirection) == HIGH ? 1 : -1;
    moving = true;
    lastUpdateMs = now;
  }

  if (now - lastUpdateMs >= updateIntervalMs) {
    lastUpdateMs = now;
    rotateServo(movementDirection);
  }
}
