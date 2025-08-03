// ASMC 04B SERVO MOTOR CONTROL VIA SERIAL MONITOR
//CIRCUIT : RC MODE  : 1ms (JUMPER POsition Refer Datasheet)
// +B -B  (ASMC) : 12 Volt
// GND    (ASMC) - GND (ARDUINO)
// SIGNAL (ASMC) - 9 (ARDUINO)


#include <Servo.h>

Servo motor;
const int motorPin = 9;

const int rotate60Time = 1000;    
const int rotate180Time = 1000;   

void setup() {
  Serial.begin(115200); // Initialize serial communication
  motor.attach(motorPin);
  zeroMotor(); // Start at zero position
  delay(2000); // Wait for stability
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == '0') {
      zeroMotor();
    } else if (cmd == '1') {
      rotate60();
    } else if (cmd == '2') {
      rotate180();
    }
  }
}

void zeroMotor() {
  Serial.println("zeroMotor() :: "); 
  motor.writeMicroseconds(1500); 
}

void rotate60() {
  Serial.println("rotate60() :: ");
  motor.write(120); // Move to 60 degrees (anticlockwise)
}

void rotate180() {
  Serial.println("rotate180() :: ");
  motor.write(180); // Move to 180 degrees (anticlockwise)
}
