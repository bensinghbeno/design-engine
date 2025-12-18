/*

VCC -> 3.3V Arduino
GND -> GND
SDA -> A4 (UNO SDA)
SCL -> A5 (UNO SCL)
INT (if present/used) -> optional digital pin (e.g., D2) — not used by this sketch
*/

#include <Wire.h>

const uint8_t AS5600_ADDR = 0x36;   // I2C address for AS5600
#define COUNTS_PER_REV 4096  // 12-bit resolution

bool initialized = false;
uint16_t prevRaw = 0;
int32_t totalTicks = 0;   // signed cumulative tick count since zero

void setup() {
  Serial.begin(115200);
  Wire.begin();  // Join I2C bus (UNO: SDA=A4, SCL=A5)
  delay(500);
  Serial.println("AS5600 Magnetic Encoder Test - Revolutions tracking");
  
  // Wait until AS5600 is detected
  Serial.print("Scanning for AS5600 at address 0x");
  Serial.print(AS5600_ADDR, HEX);
  Serial.println("...");
  
  while (true) {
    Wire.beginTransmission(AS5600_ADDR);
    if (Wire.endTransmission() == 0) {
      Serial.println("AS5600 found!");
      break; // Exit the loop once the sensor is detected
    }
    delay(1000); // Wait a second before retrying
  }
}

uint16_t readAngleRaw() {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(0x0E);  // Start address for angle high byte
  if (Wire.endTransmission() != 0) return 0xFFFF; // comms error
  
  Wire.requestFrom((uint8_t)AS5600_ADDR, (uint8_t)2); // unambiguous overload
  if (Wire.available() == 2) {
    uint8_t highByte = Wire.read();
    uint8_t lowByte = Wire.read();
    return ((highByte & 0x0F) << 8) | lowByte;  // 12-bit angle
  }
  return 0xFFFF;  // error
}

void loop() {
  uint16_t raw = readAngleRaw();
  if (raw == 0xFFFF) {
    Serial.println("Read error");
    delay(200);
    return;
  }

  if (!initialized) {
    // Treat first reading as zero reference: map current physical angle -> logical 0
    prevRaw = raw;
    totalTicks = 0;
    initialized = true;
    Serial.print("Zeroed at raw = ");
    Serial.println(raw);
    // Explicitly show start state as 0 rev +0.00 deg
    Serial.print("+");
    Serial.print(0);
    Serial.print(" rev +");
    Serial.print(0.00, 2);
    Serial.println(" deg");
    delay(200);
    return;
  }

  // compute delta with wrap correction
  int32_t delta = (int32_t)raw - (int32_t)prevRaw;
  if (delta > (COUNTS_PER_REV / 2)) {
    delta -= COUNTS_PER_REV;
  } else if (delta < -(COUNTS_PER_REV / 2)) {
    delta += COUNTS_PER_REV;
  }

  totalTicks += delta;
  prevRaw = raw;

  // compute integer revolutions and remaining angle (signed)
  int32_t revsInt = totalTicks / COUNTS_PER_REV;            // trunc toward zero
  int32_t remTicks = totalTicks % COUNTS_PER_REV;          // may be negative
  float remAngleDeg = (remTicks * 360.0f) / (float)COUNTS_PER_REV;

  // --- changed printing: show absolute values and direction ---
  // direction based on sign of totalTicks: '+' for forward, '-' for reverse, '0' if exactly zero
  char dir = (totalTicks > 0) ? '+' : (totalTicks < 0) ? '-' : '0';

  // absolute values
  uint32_t revsAbs = (revsInt >= 0) ? (uint32_t)revsInt : (uint32_t)(-revsInt);
  float remAngleAbs = (remAngleDeg >= 0.0f) ? remAngleDeg : -remAngleDeg;

  // print direction + absolute revolutions and absolute remaining angle
  if (dir != '0') Serial.print(dir);
  Serial.print(revsAbs);
  Serial.print(" rev ");

  if (dir != '0') Serial.print(dir);
  Serial.print(remAngleAbs, 2);
  Serial.println(" deg");
  // --- end changed printing ---

  delay(200);
}