#include <Servo.h>

Servo myServo;
const int servoPin = 9;
const int buttonPinRun = 6;
const int buttonPinDirection = 7;
const int minPulseUs = 500;
const int maxPulseUs = 2500;
const int centerPulseUs = 1500;
const int stepPulseUs = 4;
const unsigned long buttonPulsePeriodUs = 13500;
const unsigned long updateIntervalMs = 20;
const unsigned long buttonUpdateIntervalMs = 20;
const unsigned long debounceMs = 30;
const unsigned long startupSettleMs = 1000;
const unsigned long positionLogIntervalMs = 250;

int currentPulse = centerPulseUs;
int lastRunState = HIGH;
int movementDirection = 1;
bool armed = false;
bool moving = false;
bool centering = false;
unsigned long startupMs = 0;
unsigned long runChangedMs = 0;
unsigned long lastUpdateMs = 0;
unsigned long lastPositionLogMs = 0;
unsigned long buttonPulseRemainderUs = 0;

void logPosition(const char* event) {
  Serial.print(event);
  Serial.print(F(" target_us="));
  Serial.print(currentPulse);
  Serial.print(F(" nominal_deg="));
  Serial.println((currentPulse - minPulseUs) * 270.0 / (maxPulseUs - minPulseUs), 1);
  lastPositionLogMs = millis();
}

void rotateServo(int direction, unsigned long elapsedMs) {
  buttonPulseRemainderUs += elapsedMs * 1000UL;
  const int pulseIncrement = min(buttonPulseRemainderUs / buttonPulsePeriodUs,
                                 static_cast<unsigned long>(maxPulseUs - minPulseUs));
  buttonPulseRemainderUs %= buttonPulsePeriodUs;
  currentPulse = constrain(currentPulse + direction * pulseIncrement,
                           minPulseUs, maxPulseUs);
  myServo.writeMicroseconds(currentPulse);
}

void setup() {
  Serial.begin(115200);
  pinMode(buttonPinRun, INPUT_PULLUP);
  pinMode(buttonPinDirection, INPUT_PULLUP);
  myServo.writeMicroseconds(currentPulse);
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

  if (Serial.available() > 0) {
    const char command = Serial.read();
    if (command == 'Z' || command == 'z') {
      if (armed && runState == HIGH) {
        centering = true;
        moving = false;
        lastUpdateMs = now;
        Serial.println(F("Moving to 135 degrees. Press D6 to cancel."));
      } else {
        Serial.println(F("Release D6 and wait for startup before sending Z/z."));
      }
    }
  }

  if (centering) {
    if (runState == LOW) {
      centering = false;
      Serial.println(F("Centering cancelled."));
    } else {
      if (now - lastUpdateMs >= updateIntervalMs) {
        lastUpdateMs = now;
        currentPulse += constrain(centerPulseUs - currentPulse, -stepPulseUs, stepPulseUs);
        myServo.writeMicroseconds(currentPulse);
        if (currentPulse == centerPulseUs) {
          centering = false;
          Serial.println(F("Target reached: 135 degrees (1500 us)."));
        }
      }
      return;
    }
  }

  if (runState == HIGH) {
    if (moving) {
      logPosition("HOLD");
    }
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
    buttonPulseRemainderUs = 0;
    logPosition(movementDirection > 0 ? "FORWARD" : "REVERSE");
  }

  if (now - lastUpdateMs >= buttonUpdateIntervalMs) {
    const unsigned long elapsedMs = now - lastUpdateMs;
    lastUpdateMs = now;
    rotateServo(movementDirection, elapsedMs);
  }

  if (millis() - lastPositionLogMs >= positionLogIntervalMs) {
    logPosition("MOVING");
  }
}
