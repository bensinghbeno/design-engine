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
#define SERVOMID 300     // Maximum pulse length out of 4096
#define RAMPSTEP 2     
#define RAMPDELAY 10     

void setup() {
  Serial.begin(115200);
  Serial.println("PCA9685 Servo Test ============ ");
  delay(1000);

  pwm.begin();
  pwm.setPWMFreq(50); // Analog servos run at ~50 Hz. Set frequency to 50Hz.
}

void initMidPos()
{
  // Stop servo
  Serial.println("Min Pos Stopping");
  pwm.setPWM(SERVO_CHANNEL, 0, SERVOMID);
  delay(100);
  pwm.setPWM(SERVO_CHANNEL, 0, SERVOMID);
  delay(100);
  pwm.setPWM(SERVO_CHANNEL, 0, SERVOMID);

  pwm.setPWM(SERVO_CHANNEL, 0, 0); // Stop position
  delay(2000); // Hold for 2 seconds
}

void stopServo()
{
      // Stop servo
    Serial.println("Stopping");
    pwm.setPWM(SERVO_CHANNEL, 0, 0); // Stop position
    delay(2000); // Hold for 2 seconds
}

void loop() {

  initMidPos();

  while(1)
  {
    stopServo();

    // Gradually ramp up servo forward
    Serial.println("Ramping Forward");
    for (int pulse = SERVOMID; pulse <= SERVOMAX; pulse += RAMPSTEP) { // Increment in steps of 10
      pwm.setPWM(SERVO_CHANNEL, 0, pulse);
      delay(RAMPDELAY); // Small delay for gradual ramp-up
    }

    stopServo();

    // Gradually ramp down servo reverse
    Serial.println("Ramping Reverse");
    for (int pulse = SERVOMAX; pulse >= SERVOMID; pulse -= RAMPSTEP) { // Decrement in steps of 10
      pwm.setPWM(SERVO_CHANNEL, 0, pulse);
      delay(RAMPDELAY); // Small delay for gradual ramp-down
    }

    stopServo();

    // Gradually ramp down servo reverse
    Serial.println("Ramping Reverse");
    for (int pulse = SERVOMID; pulse >= SERVOMIN; pulse -= RAMPSTEP) { // Decrement in steps of 10
      pwm.setPWM(SERVO_CHANNEL, 0, pulse);
      delay(RAMPDELAY); // Small delay for gradual ramp-down
    }

    stopServo();

    // Gradually ramp up servo forward
    Serial.println("Ramping Forward");
    for (int pulse = SERVOMIN; pulse <= SERVOMID; pulse += RAMPSTEP) { // Increment in steps of 10
      pwm.setPWM(SERVO_CHANNEL, 0, pulse);
      delay(RAMPDELAY); // Small delay for gradual ramp-up
    }



  }
}
