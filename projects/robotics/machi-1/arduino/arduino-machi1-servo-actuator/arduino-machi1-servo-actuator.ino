#include <Wire.h>
#include <Servo.h>
#include <EEPROM.h>
#include <math.h>
#include <stddef.h>
#include <stdlib.h>

const uint8_t AS5600_ADDRESS = 0x36;
const uint8_t ANGLE_REGISTER = 0x0E;
const uint16_t COUNTS_PER_REVOLUTION = 4096;
const unsigned long DISPLAY_INTERVAL_MS = 250;
const bool manualTestMode = false;
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

struct ServoCalibration {
  uint32_t magic;
  uint16_t version;
  float centerAngle;
  float degreesPerUs;
  uint16_t checksum;
};

const uint32_t calibrationMagic = 0x4D314341UL;
const uint16_t calibrationVersion = 1;
const int calibrationOffsetUs = 100;
ServoCalibration calibration = {};
bool controlReady = false;

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

float angleDifference(float angle, float reference) {
  float difference = angle - reference;
  while (difference > 180.0f) difference -= 360.0f;
  while (difference <= -180.0f) difference += 360.0f;
  return difference;
}

uint16_t calibrationChecksum(const ServoCalibration &record) {
  const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&record);
  uint16_t checksum = 0xFFFF;
  for (size_t index = 0; index < offsetof(ServoCalibration, checksum); ++index) {
    checksum ^= static_cast<uint16_t>(bytes[index]) << 8;
    for (uint8_t bit = 0; bit < 8; ++bit) {
      checksum = (checksum & 0x8000) ? (checksum << 1) ^ 0x1021 : checksum << 1;
    }
  }
  return checksum;
}

bool validCalibration(const ServoCalibration &record) {
  const float slope = fabs(record.degreesPerUs);
  return record.magic == calibrationMagic && record.version == calibrationVersion &&
      record.checksum == calibrationChecksum(record) &&
      isfinite(record.centerAngle) && record.centerAngle >= 0.0f && record.centerAngle < 360.0f &&
      isfinite(slope) && slope >= 0.08f && slope <= 0.17f;
}

bool magnetHealthy() {
  Wire.beginTransmission(AS5600_ADDRESS);
  Wire.write(0x0B);
  if (Wire.endTransmission(false) != 0 ||
      Wire.requestFrom(AS5600_ADDRESS, (uint8_t)1) != 1) {
    Serial.println(F("FAIL: I2C status read."));
    return false;
  }
  const uint8_t status = Wire.read();
  if ((status & 0x38) != 0x20) {
    Serial.print(F("FAIL: magnet status=0x"));
    Serial.print(status, HEX);
    Serial.println(F(" (expected MD=1, ML=0, MH=0)."));
  }
  return (status & 0x38) == 0x20;
}

bool readStableAngle(float &angle) {
  uint16_t rawAngle;
  if (!magnetHealthy()) return false;
  if (!readRawAngle(rawAngle)) {
    Serial.println(F("FAIL: initial angle I2C read."));
    return false;
  }
  float reference = rawAngle * (360.0f / COUNTS_PER_REVOLUTION);
  const unsigned long started = millis();
  unsigned long windowStarted = started;
  unsigned int sampleCount = 1;
  float lowestDifference = 0.0f;
  float highestDifference = 0.0f;
  float totalDifference = 0.0f;
  while (millis() - started < 10000UL) {
    delay(20);
    if (!magnetHealthy()) return false;
    if (!readRawAngle(rawAngle)) {
      Serial.println(F("FAIL: sampled angle I2C read."));
      return false;
    }
    const float difference = angleDifference(rawAngle * (360.0f / COUNTS_PER_REVOLUTION), reference);
    lowestDifference = min(lowestDifference, difference);
    highestDifference = max(highestDifference, difference);
    if (highestDifference - lowestDifference > 0.5f) {
      reference = rawAngle * (360.0f / COUNTS_PER_REVOLUTION);
      windowStarted = millis();
      sampleCount = 1;
      lowestDifference = 0.0f;
      highestDifference = 0.0f;
      totalDifference = 0.0f;
      continue;
    }
    totalDifference += difference;
    ++sampleCount;
    if (millis() - windowStarted < 1000UL) continue;
    angle = reference + totalDifference / sampleCount;
    if (angle < 0.0f) angle += 360.0f;
    if (angle >= 360.0f) angle -= 360.0f;
    Serial.print(F("Stable angle_deg="));
    Serial.print(angle, 3);
    Serial.print(F(" wait_ms="));
    Serial.println(millis() - started);
    return true;
  }
  Serial.println(F("FAIL: no stable 1000 ms window within 10000 ms (range limit 0.5 deg)."));
  return false;
}

void attachAtPulse(int pulse) {
  pulse = constrain(pulse, minPulseUs, maxCommandPulseUs);
  noInterrupts();
  myServo.attach(servoPin, minPulseUs, maxPulseUs);
  myServo.writeMicroseconds(pulse);
  interrupts();
  currentPulse = pulse;
}

bool calibrateServo() {
  float initialAngle;
  Serial.println(F("CAL: initial sensor check; EEPROM not written yet."));
  if (!readStableAngle(initialAngle)) return false;
  Serial.println(F("Calibrating: moving near center (1400-1600 us). Buttons disabled."));
  attachAtPulse(centerPulseUs);
  if (!readStableAngle(initialAngle)) return false;
  Serial.println(F("CAL: command 1400 us, wait for stable angle."));
  myServo.writeMicroseconds(centerPulseUs - calibrationOffsetUs);
  float lowAngle;
  if (!readStableAngle(lowAngle)) return false;
  Serial.println(F("CAL: command 1600 us, wait for stable angle."));
  myServo.writeMicroseconds(centerPulseUs + calibrationOffsetUs);
  float highAngle;
  if (!readStableAngle(highAngle)) return false;
  Serial.println(F("CAL: command 1500 us, wait for stable angle."));
  myServo.writeMicroseconds(centerPulseUs);
  float centerAngle;
  if (!readStableAngle(centerAngle)) return false;

  const float span = angleDifference(highAngle, lowAngle);
  const float centerError = fabs(angleDifference(centerAngle, lowAngle) - span / 2.0f);
  Serial.print(F("CAL: span_deg="));
  Serial.print(span, 3);
  Serial.print(F(" center_error_deg="));
  Serial.println(centerError, 3);
  if (centerError > 2.0f) {
    Serial.println(F("FAIL: center consistency exceeds 2 degrees; EEPROM not written."));
    return false;
  }
  calibration = {};
  calibration.magic = calibrationMagic;
  calibration.version = calibrationVersion;
  calibration.centerAngle = centerAngle;
  calibration.degreesPerUs = span / (2.0f * calibrationOffsetUs);
  calibration.checksum = calibrationChecksum(calibration);
  Serial.print(F("CAL: degrees_per_us="));
  Serial.println(calibration.degreesPerUs, 6);
  if (!validCalibration(calibration)) {
    Serial.println(F("FAIL: invalid mapping; expected absolute slope 0.08..0.17. EEPROM not written."));
    return false;
  }

  Serial.println(F("EEPROM: writing calibration at address 0."));
  EEPROM.put(0, calibration);
  ServoCalibration stored = {};
  EEPROM.get(0, stored);
  if (!validCalibration(stored) || stored.checksum != calibration.checksum) {
    Serial.println(F("FAIL: EEPROM read-back verification."));
    return false;
  }
  currentPulse = centerPulseUs;
  Serial.println(F("Calibration saved to EEPROM."));
  return true;
}

bool initializeServo() {
  EEPROM.get(0, calibration);
  if (!validCalibration(calibration)) {
    Serial.println(F("EEPROM: no valid calibration record; starting calibration."));
    return calibrateServo();
  }

  Serial.println(F("Using EEPROM calibration; matching current AS5600 angle."));
  float angle;
  if (!readStableAngle(angle)) return false;
  const float pulse = centerPulseUs + angleDifference(angle, calibration.centerAngle) /
      calibration.degreesPerUs;
  Serial.print(F("STARTUP: matched pulse_us="));
  Serial.println(pulse, 2);
  if (!isfinite(pulse) || pulse < minPulseUs || pulse > maxCommandPulseUs) {
    Serial.println(F("FAIL: startup pulse outside permitted 0..250 degree range."));
    return false;
  }
  attachAtPulse(static_cast<int>(pulse + 0.5f));
  return true;
}

void displayAngle() {
  const unsigned long now = millis();
  if (now - lastDisplayTime < DISPLAY_INTERVAL_MS) return;
  lastDisplayTime = now;
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
  Wire.begin();

  Serial.println("Waiting for AS5600 at I2C address 0x36...");
  while (!as5600Detected()) {
    delay(1000);
  }
  Serial.println("AS5600 detected.");

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

  if (!initializeServo()) {
    myServo.detach();
    pinMode(servoPin, OUTPUT);
    digitalWrite(servoPin, LOW);
    Serial.println(F("Calibration/startup failed. Servo signal off; buttons disabled. Check sensor and mechanism, then reset."));
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
    if (!armed && now - startupMs >= startupSettleMs && now - runChangedMs >= debounceMs) {
      armed = true;
      Serial.println(F("BUTTONS ARMED. Hold D6 to move; D7 selects direction at run start."));
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