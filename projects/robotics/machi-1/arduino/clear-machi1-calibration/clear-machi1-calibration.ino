#include <EEPROM.h>

const uint8_t servoPin = 9;
bool calibrationCleared = false;
unsigned long lastReportMs = 0;

void setup() {
  digitalWrite(servoPin, LOW);
  pinMode(servoPin, OUTPUT);
  Serial.begin(115200);
  for (int address = 0; address < 4; ++address) {
    EEPROM.update(address, 0);
  }
  calibrationCleared = true;
  for (int address = 0; address < 4; ++address) {
    if (EEPROM.read(address) != 0) calibrationCleared = false;
  }
}

void loop() {
  if (millis() - lastReportMs < 1000UL) return;
  lastReportMs = millis();
  if (calibrationCleared) {
    Serial.println(F("Calibration invalidated: EEPROM bytes 0..3 verified zero. D9 LOW; no servo pulses. Reflash actuator sketch to calibrate."));
  } else {
    Serial.println(F("FAIL: EEPROM clear verification. D9 LOW; no servo pulses."));
  }
}