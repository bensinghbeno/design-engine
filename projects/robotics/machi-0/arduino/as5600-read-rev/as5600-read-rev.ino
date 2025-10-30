#include <Wire.h>

#define AS5600_ADDR 0x36
#define ANGLE_HIGH  0x0E
#define ANGLE_LOW   0x0F

volatile long revCount = 0;
uint16_t lastRaw = 0;

uint16_t readRawAngle() {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(ANGLE_HIGH);
  Wire.endTransmission(false);

  Wire.requestFrom(AS5600_ADDR, 2);
  uint8_t high = Wire.read();
  uint8_t low  = Wire.read();

  return ((high & 0x0F) << 8) | low;   // 12-bit angle (0–4095)
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);   // ✅ Set I2C to 400 kHz (fast mode)
  delay(200);

  lastRaw = readRawAngle();

  Serial.println("AS5600 Multi-turn Tracking READY @400kHz");
  Serial.println("Send ANY character to print angle once.");
}

void loop() {

  // ---- Continuous multi-turn tracking ----
  uint16_t raw = readRawAngle();

  int diff = raw - lastRaw;

  // Handle rollover (+ to – direction)
  if (diff > 2048)       revCount--;
  else if (diff < -2048) revCount++;

  lastRaw = raw;

  // ---- Check for serial request ----
  if (Serial.available()) {
    Serial.read();   // discard received character

    float angle = raw * 360.0 / 4096.0;
    float totalDeg = revCount * 360.0 + angle;

    Serial.print("Revs: ");
    Serial.print(revCount);
    Serial.print("   Angle: ");
    Serial.print(angle, 2);
    Serial.print(" deg   Total: ");
    Serial.println(totalDeg, 2);

    delay(2000);   // ✅ OK since motor is not moving during request
  }
}