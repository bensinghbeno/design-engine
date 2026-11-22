#include <Wire.h>
#include <Servo.h>
#include <math.h>
#include <stdlib.h>

const uint8_t AS5600_ADDRESS = 0x36;
const uint8_t ANGLE_REGISTER = 0x0E;
const uint16_t COUNTS_PER_REVOLUTION = 4096;
const unsigned long DISPLAY_INTERVAL_MS = 250;
const bool manualTestMode = false;
const bool potentiometerMode = true;
const int potentiometerPin = A0;
const int potentiometerDeadbandUs = 6;
const int potentiometerZeroAdc = 115;
char testCommand[24];
size_t testCommandLength = 0;
bool testCommandOverflow = false;

Servo myServo;
const int servoPin = 9;
const int buttonPinRun = 6;
const int buttonPinDirection = 7;
const int minPulseUs = 500;
const int maxPulseUs = 2500;
const float maxCommandAngle = 250.0f;
const int maxCommandPulseUs = minPulseUs + static_cast<int>(maxCommandAngle * (maxPulseUs - minPulseUs) / 270.0f + 0.5f);
const int centerPulseUs = 1500;
const int stepPulseUs = 4;
const unsigned long buttonPulsePeriodUs = 6750;
const unsigned long updateIntervalMs = 20;
const unsigned long buttonUpdateIntervalMs = 20;
const unsigned long debounceMs = 30;
const unsigned long startupSettleMs = 1000;
const unsigned long positionLogIntervalMs = 250;

bool controlReady = false;
bool potControlling = false;
int potTakeoverReading = 0;
unsigned long lastPotUpdateMs = 0;

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
unsigned long lastDisplayTime = 0;

bool as5600Detected() {
  Wire.beginTransmission(AS5600_ADDRESS);
  return Wire.endTransmission() == 0;
}

bool readRawAngle(uint16_t &rawAngle) {
  Wire.beginTransmission(AS5600_ADDRESS);
  Wire.write(ANGLE_REGISTER);
  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  if (Wire.requestFrom(AS5600_ADDRESS, (uint8_t)2) != 2) {
    return false;
  }

  const uint8_t highByte = Wire.read();
  const uint8_t lowByte = Wire.read();
  rawAngle = ((uint16_t)(highByte & 0x0F) << 8) | lowByte;
  return true;
}

void attachAtPulse(int pulse) {
  pulse = constrain(pulse, minPulseUs, maxCommandPulseUs);
  noInterrupts();
  myServo.attach(servoPin, minPulseUs, maxPulseUs);
  myServo.writeMicroseconds(pulse);
  interrupts();
  currentPulse = pulse;
}

int lastPotAverage = -1;
int lastPotTargetPulse = -1;

void logPotentiometer() {
  Serial.print(F("POT ms="));
  Serial.print(millis());
  Serial.print(F(" raw="));
  Serial.print(analogRead(potentiometerPin));
  Serial.print(F(" average="));
  Serial.print(lastPotAverage);
  Serial.print(F(" requested_us="));
  Serial.print(lastPotTargetPulse);
  Serial.print(F(" commanded_us="));
  Serial.print(currentPulse);
  Serial.print(F(" ready="));
  Serial.print(controlReady);
  Serial.print(F(" attached="));
  Serial.print(myServo.attached());
  Serial.print(F(" pot_mode="));
  Serial.print(potentiometerMode);
  Serial.print(F(" pot_active="));
  Serial.print(potControlling);
  Serial.print(F(" manual_mode="));
  Serial.println(manualTestMode);
}

void displayAngle() {
  const unsigned long now = millis();
  if (now - lastDisplayTime < DISPLAY_INTERVAL_MS) return;
  lastDisplayTime = now;
  logPotentiometer();
  uint16_t rawAngle;
  Serial.print(F("SAMPLE ms="));
  Serial.print(now);
  Serial.print(F(" target_us="));
  Serial.print(currentPulse);
  Serial.print(F(" nominal_deg="));
  Serial.print((currentPulse - minPulseUs) * 270.0f / (maxPulseUs - minPulseUs), 2);
  if (!readRawAngle(rawAngle)) {
    Serial.println(F(" error=AS5600_READ"));
    return;
  }

  const float angleDegrees = rawAngle * (360.0f / COUNTS_PER_REVOLUTION);
  Serial.print(F(" as5600_deg="));
  Serial.println(angleDegrees, 3);
}

void processTestCommand() {
  testCommand[testCommandLength] = '\0';
  char *endPointer;
  const float angle = strtod(testCommand, &endPointer);
  const bool hasNumber = endPointer != testCommand;
  while (*endPointer == ' ' || *endPointer == '\t') ++endPointer;
  if (testCommandOverflow || !hasNumber || *endPointer != '\0' ||
      !isfinite(angle) || angle < 0.0f || angle > maxCommandAngle) {
    Serial.println(F("ERROR: enter one angle from 0 to 250, followed by Enter."));
  } else {
    currentPulse = minPulseUs + static_cast<int>(angle * (maxPulseUs - minPulseUs) / 270.0f + 0.5f);
    myServo.writeMicroseconds(currentPulse);
    Serial.print(F("COMMAND ms="));
    Serial.print(millis());
    Serial.print(F(" requested_deg="));
    Serial.print(angle, 3);
    Serial.print(F(" target_us="));
    Serial.println(currentPulse);
  }
  testCommandLength = 0;
  testCommandOverflow = false;
}

void readTestCommands() {
  while (Serial.available() > 0) {
    const char incoming = Serial.read();
    if (incoming == '\r' || incoming == '\n') {
      if (testCommandLength > 0 || testCommandOverflow) processTestCommand();
    } else if (testCommandLength < sizeof(testCommand) - 1) {
      testCommand[testCommandLength++] = incoming;
    } else {
      testCommandOverflow = true;
    }
  }
}

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
                                 static_cast<unsigned long>(maxCommandPulseUs - minPulseUs));
  buttonPulseRemainderUs %= buttonPulsePeriodUs;
  currentPulse = constrain(currentPulse + direction * pulseIncrement,
                           minPulseUs, maxCommandPulseUs);
  myServo.writeMicroseconds(currentPulse);
}

void setup() {
  Serial.begin(115200);
  pinMode(buttonPinRun, INPUT_PULLUP);
  pinMode(buttonPinDirection, INPUT_PULLUP);
  pinMode(potentiometerPin, INPUT);
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  Serial.println(F("STARTUP: commanding center 135 deg / 1500 us. No calibration."));
  attachAtPulse(centerPulseUs);
  Serial.println(as5600Detected() ? F("AS5600 detected (logging only).") :
      F("AS5600 missing; controls remain available."));

  if (manualTestMode) {
    Serial.println(F("MANUAL TEST: EEPROM unchanged; buttons disabled. Commanding center 135 deg / 1500 us."));
    attachAtPulse(centerPulseUs);
    const unsigned long settleStart = millis();
    while (millis() - settleStart < 2000) displayAngle();
    while (Serial.available() > 0) Serial.read();
    controlReady = true;
    Serial.println(F("READY: enter nominal servo angle 0..250 and Enter. Start near 135; AS5600 angles are independent."));
    return;
  }

  controlReady = true;
  while (Serial.available() > 0) Serial.read();
  Serial.println(F("Ready. Release D6 for one second before running."));
  lastRunState = digitalRead(buttonPinRun);
  startupMs = millis();
  runChangedMs = startupMs;
}

void loop() {
  displayAngle();
  if (!controlReady) return;
  if (manualTestMode) {
    readTestCommands();
    return;
  }

  const unsigned long now = millis();
  const int runState = digitalRead(buttonPinRun);
  bool potSampled = false;
  if (potentiometerMode) {
    if (now - lastPotUpdateMs >= updateIntervalMs) {
      lastPotUpdateMs = now;
      potSampled = true;
      long readingTotal = 0;
      for (uint8_t sample = 0; sample < 8; ++sample) {
        readingTotal += analogRead(potentiometerPin);
      }
      lastPotAverage = readingTotal / 8;
      const int targetPulse = map(constrain(lastPotAverage, potentiometerZeroAdc, 1023),
                  potentiometerZeroAdc, 1023, minPulseUs, maxCommandPulseUs);
      lastPotTargetPulse = targetPulse;
      if (!armed || runState == LOW || moving || centering) {
        potControlling = false;
        potTakeoverReading = lastPotAverage;
      } else if (!potControlling && abs(lastPotAverage - potTakeoverReading) >= 8) {
        potControlling = true;
        Serial.println(F("POT ACTIVE"));
      }
    }
  }
  if (runState != lastRunState) {
    lastRunState = runState;
    runChangedMs = now;
  }

  static int reportedRunState = -1;
  if (now - runChangedMs >= debounceMs && runState != reportedRunState) {
    reportedRunState = runState;
    Serial.print(F("D6="));
    Serial.print(runState == LOW ? F("PRESSED") : F("RELEASED"));
    Serial.print(F(" D7="));
    Serial.print(digitalRead(buttonPinDirection));
    Serial.print(F(" armed="));
    Serial.println(armed);
    if (runState == LOW && !armed) {
      Serial.println(F("Press ignored: release D6, wait for BUTTONS ARMED, then press again."));
    }
  }

  if (Serial.available() > 0) {
    const char command = Serial.read();
    if (command == 'Z' || command == 'z') {
      if (armed && runState == HIGH) {
        centering = true;
        potControlling = false;
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
      potControlling = false;
      potTakeoverReading = lastPotAverage;
    }
    moving = false;
    lastUpdateMs = now;
    if (!armed && now - startupMs >= startupSettleMs && now - runChangedMs >= debounceMs) {
      armed = true;
      potTakeoverReading = lastPotAverage;
      Serial.println(F("BUTTONS ARMED. D6 moves; D7 sets direction. Turn A0 pot to take control."));
    }
    if (armed && potentiometerMode && potControlling && potSampled &&
        (abs(lastPotTargetPulse - currentPulse) > potentiometerDeadbandUs ||
         (lastPotTargetPulse == minPulseUs && currentPulse != minPulseUs))) {
      currentPulse += constrain(lastPotTargetPulse - currentPulse, -stepPulseUs, stepPulseUs);
      myServo.writeMicroseconds(currentPulse);
    }
    return;
  }

  if (!armed || now - runChangedMs < debounceMs) {
    return;
  }

  if (!moving) {
    potControlling = false;
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