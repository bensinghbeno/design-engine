/*
SG90 SERVO

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
#define SERVOMIN 100     // Minimum pulse length out of 4096
#define SERVOMAX 500     // Maximum pulse length out of 4096
#define RAMPSTEP 20     

void setup() {
  Serial.begin(115200);
  Serial.println("PCA9685 Servo Test ============ ");
  delay(1000);

  pwm.begin();
  pwm.setPWMFreq(50); // Analog servos run at ~50 Hz. Set frequency to 50Hz.
}

void loop() {
  // Gradually ramp up servo forward
  Serial.println("Ramping Forward");
  for (int pulse = SERVOMIN; pulse <= SERVOMAX; pulse += 10) { // Increment in steps of 10
    pwm.setPWM(SERVO_CHANNEL, 0, pulse);
    delay(100); // Small delay for gradual ramp-up
  }

  // Stop servo
  Serial.println("Stopping");
  pwm.setPWM(SERVO_CHANNEL, 0, 0); // Stop position
  delay(2000); // Hold for 2 seconds

  // Gradually ramp down servo reverse
  Serial.println("Ramping Reverse");
  for (int pulse = SERVOMAX; pulse >= SERVOMIN; pulse -= 10) { // Decrement in steps of 10
    pwm.setPWM(SERVO_CHANNEL, 0, pulse);
    delay(100); // Small delay for gradual ramp-down
  }

  // Stop servo
  Serial.println("Stopping");
  pwm.setPWM(SERVO_CHANNEL, 0, 0); // Stop position
  delay(2000); // Hold for 2 seconds
}
