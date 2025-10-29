/*
AS5600 to MKR WiFi 1010 (I2C Communication):
AS5600 VCC → MKR *5V
AS5600 GND → MKR GND
AS5600 SCL → MKR SCL (Pin A21)
AS5600 SDA → MKR SDA (Pin A22)

L298N Pin	Connect To (MKR WiFi 1010)	Description
ENA	                  D4	PWM speed / enable
IN1	                  D2	Motor direction 1
IN2	                  D3	Motor direction 2
12V	External power (motor supply, e.g. 9–12 V)	Power for motor
GND	Common ground with MKR	Ground reference
OUT1, OUT2	Motor terminals	Motor output
5V (from L298 board)	Do NOT connect to MKR 5 V	(L298 onboard regulator may not match MKR’s 3.3 V logic)
*/
#include <Wire.h>

#define AS5600_ADDR 0x36
#define ANGLE_HIGH  0x0E
#define ANGLE_LOW   0x0F

void setup() {
  Serial.begin(115200);
  Wire.begin();   // SDA=A22, SCL=A21 on MKR WiFi 1010
  delay(200);
  Serial.println("AS5600 Angle Read Test");
}

uint16_t readRawAngle() {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(ANGLE_HIGH);
  Wire.endTransmission(false);

  Wire.requestFrom(AS5600_ADDR, 2);
  uint8_t high = Wire.read();
  uint8_t low  = Wire.read();

  return ((high & 0x0F) << 8) | low;  // 12-bit angle (0-4095)
}

void rotateMotor(int milliseconds) {
  digitalWrite(2, HIGH);  // Set IN1 to HIGH
  digitalWrite(3, LOW);   // Set IN2 to LOW
  analogWrite(4, 255);    // Set ENA to 50% duty cycle (adjust speed as needed)

  delay(milliseconds);    // Rotate for the specified duration

  analogWrite(4, 0);      // Stop the motor
  digitalWrite(2, LOW);   // Reset IN1
  digitalWrite(3, LOW);   // Reset IN2
}

void loop() {
  if (Serial.available() > 0) {
    int milliseconds = Serial.parseInt();  // Read input from Serial and convert to integer
    Serial.print("Received: ");
    Serial.println(milliseconds);

    rotateMotor(milliseconds);  // Rotate motor for the specified duration
  }

  uint16_t raw = readRawAngle();
  float angleDeg = raw * 360.0 / 4096.0;

  Serial.print("Raw: ");
  Serial.print(raw);
  Serial.print("\tAngle: ");
  Serial.print(angleDeg, 2);
  Serial.println(" deg");

  delay(1000);   // update every second
}
