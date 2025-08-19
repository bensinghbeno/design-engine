#include <Servo.h>

const int SIGNAL_PIN = 22;
Servo myServo;

void setup() {
  myServo.attach(SIGNAL_PIN);
  Serial.begin(115200);
  Serial.println("Enter 1 for forward, 2 for reverse:");
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == '1') {
      myServo.write(180); // Forward
      Serial.println("Forward");
    } else if (cmd == '2') {
      myServo.write(0); // Reverse
      Serial.println("Reverse");
    }
  }
}