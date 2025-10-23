#include <Wire.h>

#define AS5600_ADDR 0x36   // I2C address for AS5600

void setup() {
  Serial.begin(9600);
  Wire.begin();  // Join I2C bus
  delay(500);
  Serial.println("AS5600 Magnetic Encoder Test");
}

uint16_t readAngleRaw() {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(0x0E);  // Start address for angle high byte
  Wire.endTransmission();
  
  Wire.requestFrom(AS5600_ADDR, 2);
  if (Wire.available() == 2) {
    uint8_t highByte = Wire.read();
    uint8_t lowByte = Wire.read();
    return ((highByte & 0x0F) << 8) | lowByte;  // 12-bit angle
  }
  return 0xFFFF;  // error
}

void loop() {
  uint16_t rawAngle = readAngleRaw();
  if (rawAngle != 0xFFFF) {
    float angleDeg = (rawAngle * 360.0) / 4096.0;  // Convert to degrees
    Serial.print("Raw: ");
    Serial.print(rawAngle);
    Serial.print(" | Angle: ");
    Serial.print(angleDeg, 2);
    Serial.println("°");
  } else {
    Serial.println("Read error");
  }
  delay(200);
}