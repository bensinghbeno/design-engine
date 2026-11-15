#include <Servo.h>

Servo myServo;  // Create servo object
const int servoPin = 9;  // Connect signal wire to digital pin 9

void setup() {
  myServo.attach(servoPin, 500, 2500);
}

void loop() {
  myServo.writeMicroseconds(500);
  delay(2000);        // Wait 2 seconds

  myServo.writeMicroseconds(1167);
  delay(2000);

  myServo.writeMicroseconds(1833);
  delay(2000);

  myServo.writeMicroseconds(2500);
  delay(2000);        // Wait 2 seconds

  myServo.writeMicroseconds(1833);
  delay(2000);

  myServo.writeMicroseconds(1167);
  delay(2000);

}
