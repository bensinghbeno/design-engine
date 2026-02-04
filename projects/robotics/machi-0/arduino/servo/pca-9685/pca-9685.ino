/*
SG90 SERVO

wokwi::

diagram.json:
{
  "version": 1,
  "author": "Gemini",
  "editor": "wokwi",
  "parts": [
    { "type": "wokwi-arduino-uno", "id": "uno", "top": 350, "left": 100, "attrs": {} },
    { "type": "chip-pca9685", "id": "pca", "top": 452.22, "left": 417.6, "attrs": {} },
    { "type": "wokwi-servo", "id": "servo0", "top": 622, "left": 748.8, "attrs": {} },
    { "type": "wokwi-vcc", "id": "pwr", "top": 691.96, "left": 384, "attrs": { "voltage": "5" } }
  ],
  "connections": [
    [ "uno:GND.1", "pca:GND", "black", [ "v-20", "h168.5", "v256.2" ] ],
    [ "uno:5V", "pca:VCC", "limegreen", [ "v92.1", "h277.6" ] ],
    [ "uno:A4", "pca:SDA", "blue", [ "v82.5", "h191.6" ] ],
    [ "uno:A5", "pca:SCL", "orange", [ "v72.9", "h153.3" ] ],
    [ "pwr:VCC", "pca:V+", "red", [ "h-48", "v-57.6" ] ],
    [ "pwr:GND", "pca:GND", "black", [ "v-110", "h-60" ] ],
    [ "pca:PWM0", "servo0:PWM", "orange", [ "v-20" ] ],
    [ "pca:V+", "servo0:VCC", "red", [ "v-10", "h50" ] ]
  ],
  "dependencies": {}
}

pca9685.chip.json:

{
  "name": "pca9685",
  "pins": [
    "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "GND", "OE", "SCL", "SDA", "VCC", "V+",
    "PWM0", "PWM1", "PWM2", "PWM3", "", "PWM4", "PWM5", "PWM6", "PWM7", 
    "", "", "PWM8", "PWM9", "PWM10", "PWM11", "", "PWM12", "PWM13", "PWM14", "PWM15"
  ],
  "labels": [
    ["GND", "GND", "white", "black"],
    ["OE", "OE", "white", "black"],
    ["SCL", "SCL", "white", "black"],
    ["SDA", "SDA", "white", "black"],
    ["VCC", "VCC", "white", "black"],
    ["V+", "V+", "white", "red"],
    ["PWM0", "0", "yellow", "black"],
    ["PWM1", "1", "yellow", "black"],
    ["PWM2", "2", "yellow", "black"],
    ["PWM3", "3", "yellow", "black"],
    ["PWM4", "4", "yellow", "black"],
    ["PWM5", "5", "yellow", "black"],
    ["PWM6", "6", "yellow", "black"],
    ["PWM7", "7", "yellow", "black"],
    ["PWM8", "8", "yellow", "black"],
    ["PWM9", "9", "yellow", "black"],
    ["PWM10", "10", "yellow", "black"],
    ["PWM11", "11", "yellow", "black"],
    ["PWM12", "12", "yellow", "black"],
    ["PWM13", "13", "yellow", "black"],
    ["PWM14", "14", "yellow", "black"],
    ["PWM15", "15", "yellow", "black"]
  ],
  "controls": [],
  "showPinLabels": true
}

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
#define RAMPDELAY 5     

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
