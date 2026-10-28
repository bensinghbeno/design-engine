#include <Wire.h>
#include <stdlib.h>

const uint8_t AS5600_ADDRESS = 0x36;
const uint8_t ANGLE_REGISTER = 0x0E;
const uint16_t COUNTS_PER_REVOLUTION = 4096;
const unsigned long DISPLAY_INTERVAL_MS = 250;

const uint8_t STEP_PIN = 3;
const uint8_t DIR_PIN = 2;
const uint8_t ENABLE_PIN = 4;
const uint8_t BUTTON_PIN_DIRECTION = 7;
const uint8_t BUTTON_PIN_RUN = 6;
const int STEPS_PER_REVOLUTION = 400;
const unsigned long POSITIONING_RPM = 200;
const unsigned long STARTING_RPM = 100;
const unsigned long BUTTON_RPM = 500;
const int DIR_CW = LOW;
const int DIR_ACW = HIGH;
const int DIR_FOR_INCREASING_ANGLE = DIR_CW;
const unsigned int PULSE_WIDTH_US = 50;
const unsigned long STEP_INTERVAL_US =
  (60UL * 1000000UL) / ((unsigned long)STEPS_PER_REVOLUTION * POSITIONING_RPM);
const unsigned long BUTTON_STEP_INTERVAL_US =
  (60UL * 1000000UL) / ((unsigned long)STEPS_PER_REVOLUTION * BUTTON_RPM);
const unsigned long MAX_STEP_INTERVAL_US =
  (60UL * 1000000UL) / ((unsigned long)STEPS_PER_REVOLUTION * STARTING_RPM);
const unsigned long RAMP_STEP_US = 500;
const float DECELERATION_RANGE_DEGREES = 45.0f;
const float ANGLE_TOLERANCE_DEGREES = 1.0f;
const size_t COMMAND_BUFFER_SIZE = 24;

unsigned long lastDisplayTime = 0;
unsigned long lastStepTime = 0;
unsigned long currentStepIntervalUs = MAX_STEP_INTERVAL_US;
float targetAngle = 0.0f;
bool targetActive = false;
bool holdEnabled = true;
char commandBuffer[COMMAND_BUFFER_SIZE];
size_t commandLength = 0;
bool commandOverflow = false;

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

float shortestAngleError(float target, float current) {
  float error = target - current;
  while (error > 180.0f) error -= 360.0f;
  while (error <= -180.0f) error += 360.0f;
  return error;
}

void finishMove(float currentAngle) {
  targetActive = false;
  if (!holdEnabled) {
    digitalWrite(ENABLE_PIN, LOW);
  }
  Serial.print("Target reached at ");
  Serial.print(currentAngle, 2);
  Serial.println(" deg");
}

void processCommand() {
  commandBuffer[commandLength] = '\0';
  if (commandOverflow) {
    Serial.println("Input too long. Enter an angle from 0 to 360.");
  } else if (commandLength == 1 && (commandBuffer[0] == 'E' || commandBuffer[0] == 'e')) {
    holdEnabled = true;
    digitalWrite(ENABLE_PIN, HIGH);
    Serial.println("HOLD ENABLED");
  } else if (commandLength == 1 && (commandBuffer[0] == 'X' || commandBuffer[0] == 'x')) {
    holdEnabled = false;
    if (!targetActive) digitalWrite(ENABLE_PIN, LOW);
    Serial.println("HOLD DISABLED");
  } else {
    char *endPointer;
    const float requestedAngle = (float)strtod(commandBuffer, &endPointer);
    while (*endPointer == ' ' || *endPointer == '\t' || *endPointer == '\r') ++endPointer;

    if (endPointer == commandBuffer || *endPointer != '\0' ||
        !(requestedAngle >= 0.0f && requestedAngle <= 360.0f)) {
      Serial.println("Invalid input. Enter a target angle from 0 to 360 degrees.");
    } else {
      targetAngle = requestedAngle >= 360.0f ? 0.0f : requestedAngle;
      targetActive = true;
      currentStepIntervalUs = MAX_STEP_INTERVAL_US;
      lastStepTime = micros();
      digitalWrite(ENABLE_PIN, HIGH);
      Serial.print("Moving to ");
      Serial.print(targetAngle, 2);
      Serial.println(" deg");
    }
  }

  commandLength = 0;
  commandOverflow = false;
}

void readSerialCommands() {
  while (Serial.available() > 0) {
    const char incoming = (char)Serial.read();
    if (incoming == '\n') {
      processCommand();
    } else if (incoming != '\r') {
      if (commandLength < COMMAND_BUFFER_SIZE - 1) {
        commandBuffer[commandLength++] = incoming;
      } else {
        commandOverflow = true;
      }
    }
  }
}

void moveTowardTarget(float currentAngle, unsigned long nowMicros) {
  if (!targetActive) return;

  const float error = shortestAngleError(targetAngle, currentAngle);
  const float remainingDegrees = error >= 0.0f ? error : -error;
  if (error >= -ANGLE_TOLERANCE_DEGREES && error <= ANGLE_TOLERANCE_DEGREES) {
    finishMove(currentAngle);
    return;
  }

  unsigned long desiredIntervalUs = STEP_INTERVAL_US;
  if (remainingDegrees < DECELERATION_RANGE_DEGREES) {
    const float decelerationProgress =
        (DECELERATION_RANGE_DEGREES - remainingDegrees) / DECELERATION_RANGE_DEGREES;
    desiredIntervalUs += (unsigned long)(decelerationProgress *
        (MAX_STEP_INTERVAL_US - STEP_INTERVAL_US));
  }

  if (currentStepIntervalUs > desiredIntervalUs) {
    const unsigned long difference = currentStepIntervalUs - desiredIntervalUs;
    currentStepIntervalUs -= difference > RAMP_STEP_US ? RAMP_STEP_US : difference;
  } else if (currentStepIntervalUs < desiredIntervalUs) {
    const unsigned long difference = desiredIntervalUs - currentStepIntervalUs;
    currentStepIntervalUs += difference > RAMP_STEP_US ? RAMP_STEP_US : difference;
  }

  if (nowMicros - lastStepTime < currentStepIntervalUs) return;
  lastStepTime = nowMicros;

  const int direction = error > 0.0f
      ? DIR_FOR_INCREASING_ANGLE
      : (DIR_FOR_INCREASING_ANGLE == DIR_CW ? DIR_ACW : DIR_CW);
  digitalWrite(DIR_PIN, direction);
  delayMicroseconds(5);
  digitalWrite(STEP_PIN, LOW);
  delayMicroseconds(PULSE_WIDTH_US);
  digitalWrite(STEP_PIN, HIGH);
}

bool runButtonControl(unsigned long nowMicros) {
  if (digitalRead(BUTTON_PIN_RUN) != LOW) {
    if (!targetActive && !holdEnabled) {
      digitalWrite(ENABLE_PIN, LOW);
    }
    return false;
  }

  if (targetActive) {
    targetActive = false;
    Serial.println("Angle target canceled by button control.");
  }

  digitalWrite(ENABLE_PIN, HIGH);
  const int direction = digitalRead(BUTTON_PIN_DIRECTION) == HIGH ? DIR_CW : DIR_ACW;
  digitalWrite(DIR_PIN, direction);

  if (nowMicros - lastStepTime >= BUTTON_STEP_INTERVAL_US) {
    lastStepTime = nowMicros;
    delayMicroseconds(5);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(PULSE_WIDTH_US);
    digitalWrite(STEP_PIN, HIGH);
  }

  return true;
}

void setup() {
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(BUTTON_PIN_DIRECTION, INPUT_PULLUP);
  pinMode(BUTTON_PIN_RUN, INPUT_PULLUP);
  digitalWrite(STEP_PIN, HIGH);
  digitalWrite(DIR_PIN, HIGH);
  digitalWrite(ENABLE_PIN, HIGH);

  Serial.begin(115200);
  Wire.begin();

  Serial.println("Waiting for AS5600 at I2C address 0x36...");
  while (!as5600Detected()) {
    delay(1000);
  }

  Serial.println("AS5600 detected. Enter a target angle from 0 to 360 degrees.");
  Serial.println("Set Serial Monitor line ending to Newline. E enables holding; X disables holding.");
}

void loop() {
  readSerialCommands();
  const bool buttonRunning = runButtonControl(micros());
  if (buttonRunning) return;

  uint16_t rawAngle;
  if (!readRawAngle(rawAngle)) {
    if (millis() - lastDisplayTime >= DISPLAY_INTERVAL_MS) {
      lastDisplayTime = millis();
      Serial.println("AS5600 read error");
    }
    return;
  }

  const float angleDegrees = rawAngle * (360.0f / COUNTS_PER_REVOLUTION);
  moveTowardTarget(angleDegrees, micros());

  const unsigned long now = millis();
  if (now - lastDisplayTime >= DISPLAY_INTERVAL_MS) {
    lastDisplayTime = now;
    Serial.print("Angle: ");
    Serial.print(angleDegrees, 2);
    Serial.println(" deg");
  }
}
