/*
VCC ->  3.3V UNO
GND -> GND
SDA -> A4 (UNO SDA)
SCL -> A5 (UNO SCL)
INT (if present/used) -> optional digital pin (e.g., D2) — not used by this sketch
*/

#include <Wire.h>

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nI2C Scanner for Arduino Uno/Nano");

  Wire.begin();
  Wire.setClock(100000);      // Use 100 kHz for reliability
}

void loop() {
  byte error, address;
  int nDevices = 0;
  Serial.println("Scanning--...");

  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      nDevices++;
    }
  }

  if (nDevices == 0)
    Serial.println("NOT FOUND\n");
  else
    Serial.println("Done\n");

  delay(3000);
}
