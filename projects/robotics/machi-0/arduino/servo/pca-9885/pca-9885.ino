/*

Diagram:

      Arduino Uno
         ┌────────────┐
         | 5V   ──┐   │
         | GND  ──┼───┐
         | SDA A4 ─┘   │
         | SCL A5 ─────┘
         └────────────┘
               │
               ▼
        ┌───────────────────┐
        │   PCA9685 Board   │
        │                   │
Arduino 5V ─▶ VCC (logic)   │
GND ───────▶ GND ───────────┤───┐
SDA ──────▶ SDA             │   │
SCL ──────▶ SCL             │   │
External PSU + ─▶ V+ ───────┘   │
External PSU GND ──▶ GND ───────┘
CH0 PWM output ────▶ Servo SIGNAL
        ┌───────────────────┐
        │       Servo       │
        │ Red   ──┐         │
        │ Black ──┴─────────┤ GND (common)
        │ Orange ──▶ Signal │
        └───────────────────┘


*/

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>



// Create the PCA9685 object
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

#define SERVO_CHANNEL 0  // Using CH0 on PCA9685
#define SERVOMIN 150     // Minimum pulse length out of 4096
#define SERVOMAX 600     // Maximum pulse length out of 4096

void setup() {
  Serial.begin(9600);
  Serial.println("PCA9685 Servo Test");

  pwm.begin();
  pwm.setPWMFreq(100); // Analog servos run at ~50 Hz
}

void loop() {
  // Move servo "forward" (adjust values as needed)
  Serial.println("Moving Forward");
  pwm.setPWM(SERVO_CHANNEL, 0, SERVOMAX); // Forward position
  delay(1000); // Hold for 1 second

  // Optional: return to neutral / start position
  pwm.setPWM(SERVO_CHANNEL, 0, SERVOMIN); // Reverse / start
  delay(1000); // Hold for 1 second
}
