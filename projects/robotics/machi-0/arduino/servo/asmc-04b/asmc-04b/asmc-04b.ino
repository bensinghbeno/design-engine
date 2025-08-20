/* Circuit Connections

Jumper::::::
0(p   p)(b2)  0 0 0
0(b1 b1)(b2)  S + -
Arduino::::: 22 + -
*/

#include <Servo.h>
#include <IBusBM.h>

// ----- RC Input -----
IBusBM ibus;

// ----- Servo Motor -----
const int SIGNAL_PIN = 22;
Servo myServo;
const int CENTER_POS = 90; // Center position
const int ROTATE_ANGLE = 3; // Degrees to rotate

// ----- Variables -----
char inChar = 0;             // Serial character input
bool commandSet = false;     // Track whether any command was activated
const int speedMin = 255;
int currentAngle = CENTER_POS; // Track current servo angle
unsigned long lastMoveTime = 0;
const unsigned long moveInterval = 500; // milliseconds between moves


void setup() {
  myServo.attach(SIGNAL_PIN);
  myServo.write(CENTER_POS); // Start at center
  Serial.begin(115200);
  Serial.println("Enter 1 for +30°, 2 for -30°:");

  // Start serial communication
  Serial.begin(115200);
  ibus.begin(Serial1);      // iBUS RX on Serial1 (Pin 19 on Mega)  
}


// ===== MAIN LOOP =====
void loop() {
  commandSet = false;

  // --- Check Serial Command ---
  if (Serial.available()) {
    delay(10);
    inChar = (char)Serial.read();

    switch (inChar) {
      case '0': stopMotor();       break;
      case '1': forward(); break;
      case '2': reverse(); break;
    }

    commandSet = true;
  }

  // --- RC Input Check (Priority Only If No Serial Command Issued) ---
  if (!commandSet) {
    int ch2Value = ibus.readChannel(1); // CH2 (Throttle)
    bool rcAction = false;

    unsigned long now = millis();
    if (now - lastMoveTime > moveInterval) {
      if (ch2Value >= 1000 && ch2Value <= 1250) {
        reverse();
        rcAction = true;
        lastMoveTime = now;
      } else if (ch2Value >= 1750 && ch2Value <= 2000) {
        forward();
        rcAction = true;
        lastMoveTime = now;
      }
    }

    if (!rcAction) {
      stopMotor();
    }
  }
}

// Motor control functions
void forward() {
  currentAngle += ROTATE_ANGLE;
  if (currentAngle > 180) currentAngle = 180; // Limit to max angle
  myServo.write(currentAngle);
  Serial.print("Rotated to ");
  Serial.println(currentAngle);
}

void reverse() {
  currentAngle -= ROTATE_ANGLE;
  if (currentAngle < 0) currentAngle = 0; // Limit to min angle
  myServo.write(currentAngle);
  Serial.print("Rotated to ");
  Serial.println(currentAngle);
}

void stopMotor() {
  // Optionally return to center or hold position
  // myServo.write(CENTER_POS);
  Serial.println("Command: Stop");
}
