#include <IBusBM.h>
#include <Cytron_SmartDriveDuo.h>

// ----- SmartDriveDuo Pin Definitions -----
#define IN1 4
#define AN1 5
#define AN2 6
#define IN2 7

Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);

// ----- RC Input -----
IBusBM ibus;

// ----- Variables -----
char inChar = 0;             // Serial character input
signed int speedLeft = 0;    // Final left motor speed
signed int speedRight = 0;   // Final right motor speed
bool commandSet = false;     // Track whether any command was activated
const int speedMin = 100;
// ===== COMMAND FUNCTIONS =====

void doLongForward() {
  speedLeft = -speedMin;
  speedRight = speedMin;
  Serial.println("::LONG FORWARD");
  smartDriveDuo30.control(speedLeft, speedRight);
  delay(1000);
}

void doLongReverse() {
  speedLeft = speedMin;
  speedRight = -speedMin;
  Serial.println(":: LONG REVERSE");
  smartDriveDuo30.control(speedLeft, speedRight);
  delay(1000);
}

void doLongTurnLeft() {
  speedLeft = speedMin;
  speedRight = speedMin;
  Serial.println("::LONG TURN LEFT");
  smartDriveDuo30.control(speedLeft, speedRight);
  delay(500);
}

void doLongTurnRight() {
  speedLeft = -speedMin;
  speedRight = -speedMin;
  Serial.println("::LONG TURN RIGHT");
  smartDriveDuo30.control(speedLeft, speedRight);
  delay(500);
}


void doStop() {
  speedLeft = 0;
  speedRight = 0;
  smartDriveDuo30.control(speedLeft, speedRight);  // <-- ADD THIS LINE
  Serial.println(":: STOP");
}

void doForward() {
  speedLeft = -speedMin;
  speedRight = speedMin;
  Serial.println(":: FORWARD");
}

void doReverse() {
  speedLeft = speedMin;
  speedRight = -speedMin;
  Serial.println(":: REVERSE");
}

void doLeftTurn() {
  speedLeft = speedMin;
  speedRight = speedMin;
  Serial.println(":: LEFT TURN");
}

void doRightTurn() {
  speedLeft = -speedMin;
  speedRight = -speedMin;
  Serial.println(":: RIGHT TURN");
}

// ===== SETUP =====
void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(AN1, OUTPUT);
  pinMode(AN2, OUTPUT);
  pinMode(IN2, OUTPUT);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(AN1, 0);
  analogWrite(AN2, 0);

  Serial.begin(115200);     // Serial monitor
  ibus.begin(Serial1);      // iBUS RX on Serial1 (Pin 19 on Mega)

  delay(1500);
  Serial.println("====== ARDUINO MEGA: SYSTEM INIT COMPLETE =======");
}

// ===== MAIN LOOP =====
void loop() {
  commandSet = false;  // Reset command flag

  // --- Check Serial Command ---
  if (Serial.available()) {
    delay(10);
    inChar = (char)Serial.read();

  switch (inChar) {
    case '0':
      doStop();
      break;

    case '1':
      doLongReverse();
      doStop();        // Stop after duration
      break;

    case '2':
      doLongForward();
      doStop();
      break;

    case '3':
      doLongTurnLeft();
      doStop();
      break;

    case '4':
      doLongTurnRight();
      doStop();
      break;
  }


    commandSet = true;  // Serial input takes control
  }

  // --- RC Input Check (Priority Only If No Serial Command Issued) ---
  if (!commandSet) {
    int ch1Value = ibus.readChannel(0); // CH1 (Steering)
    int ch2Value = ibus.readChannel(1); // CH2 (Throttle)

    bool rcAction = false;

    if (ch2Value >= 1000 && ch2Value <= 1250) {
      doReverse();
      rcAction = true;
    } else if (ch2Value >= 1750 && ch2Value <= 2000) {
      doForward();
      rcAction = true;
    }

    if (ch1Value >= 1000 && ch1Value <= 1250) {
      doLeftTurn();
      rcAction = true;
    } else if (ch1Value >= 1750 && ch1Value <= 2000) {
      doRightTurn();
      rcAction = true;
    }

    if (!rcAction) {
      doStop();
    }
  }

  // --- Send Command to Motor Driver (Only Once) ---

  delay(100);
}
