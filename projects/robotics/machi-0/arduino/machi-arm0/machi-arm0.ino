// L298 Motor Driver with Arduino Serial Control
// Command from Serial Monitor:
// 0 = Stop motor
// 1 = Forward for 1 second
// 2 = Reverse for 1 second

#include <IBusBM.h>

// ----- RC Input -----
IBusBM ibus;
int ch1Value;
int ch2Value;
int ch3Value;
int ch4Value;
int ch5Value;
int ch6Value;
int ch7Value;
int ch8Value;

// Pin definitions
const int ENA = 10;  // Motor A enable (already used)
const int IN1 = 8;   // Motor A IN1 (already used)
const int IN2 = 9;   // Motor A IN2 (already used)

const int ENB = 13;  // Motor B enable (PWM)
const int IN3 = 11;  // Motor B IN3
const int IN4 = 12;  // Motor B IN4

// ----- Variables -----
char inChar = 0;             // Serial character input
bool commandSet = false;     // Track whether any command was activated
const int speedMin = 200;
const int rcThrottleDelay  = 1000; // ms

void setup() {
  // Set motor control pins as output
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Start serial communication
  Serial.begin(115200);
  ibus.begin(Serial1);      // iBUS RX on Serial1 (Pin 19 on Mega)  
  Serial.println("Enter command: 0=Stop, 1=Forward 1s, 2=Reverse 1s");
}
// ===== MAIN LOOP =====
void loop() {

  // Read and print channel values (first 8 channels)
  ch1Value = ibus.readChannel(0); // UpperArmJoint-Roll-LR
  Serial.print("Ch1 ");
  Serial.print(ch1Value);
  Serial.print(" | ");

  ch2Value = ibus.readChannel(1); // ForeArmJoint-Pitch-LR
  Serial.print("Ch2 ");
  Serial.print(ch2Value);
  Serial.print(" | ");

  ch3Value = ibus.readChannel(2); // ForeArmJoint-Pitch-LR
  Serial.print("Ch3 ");
  Serial.print(ch3Value);
  Serial.print(" | ");

  ch4Value = ibus.readChannel(3); // ForeArmJoint-Pitch-LR
  Serial.print("Ch4 ");
  Serial.print(ch4Value);
  Serial.print(" | ");

  Serial.print("Ch5 ");
  ch5Value = ibus.readChannel(4); // ForeArmJoint-Pitch-LR
  Serial.print(ch5Value);
  Serial.print(" | ");

  ch6Value = ibus.readChannel(5); // ForeArmJoint-Pitch-LR
  Serial.print("Ch6 ");
  Serial.print(ch6Value);
  Serial.print(" | ");

  ch7Value = ibus.readChannel(6); // ForeArmJoint-Pitch-LR
  Serial.print("Ch7 ");
  Serial.print(ch7Value);
  Serial.print(" | ");

  ch8Value = ibus.readChannel(7); // ForeArmJoint-Pitch-LR
  Serial.print("Ch8 ");
  Serial.print(ch8Value);
  Serial.print(" | ");

  Serial.println();
  delay(100);

  commandSet = false;  // Reset command flag

  // --- Check Serial Command ---
  if (Serial.available()) {
    delay(10);
    inChar = (char)Serial.read();

    switch (inChar) {
      case '0': stopAllMotors();       break;
      case '1': forward(speedMin); break;
      case '2': reverse(speedMin); break;
    }

    commandSet = true;  // Serial input takes control
  }

  // --- RC Input Check (Priority Only If No Serial Command Issued) ---
  if (!commandSet) {

    bool rcAction = false;

    if (ch1Value >= 1000 && ch1Value <= 1250) {
      upperArmJointRollLeft(speedMin);
      rcAction = true;
    } else if (ch1Value >= 1750 && ch1Value <= 2000) {
      upperArmJointRollRight(speedMin);
      rcAction = true;
    } else if (ch2Value >= 1000 && ch2Value <= 1250) {
      foreArmJointPitchUp(speedMin);
      rcAction = true;
    } else if (ch2Value >= 1750 && ch2Value <= 2000) {
      foreArmJointPitchDown(speedMin);
      rcAction = true;
    }

    //delay(rcThrottleDelay);
    //stopMotor();

    // if (ch1Value >= 1000 && ch1Value <= 1450) {
    //   doLeftTurn();
    //   rcAction = true;
    // } else if (ch1Value >= 1550 && ch1Value <= 2000) {
    //   doRightTurn();
    //   rcAction = true;
    // }

    if (!rcAction) {
      stopUpperArmJointMotor();
      stopForeArmJointMotor();
    }
  }

}

// ARM control functions
void upperArmJointRollLeft(int speed) {
  Serial.println("Command: upperArmJointRollLeft");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, speed);
}

void upperArmJointRollRight(int speed) {
  Serial.println("Command: upperArmJointRollRight");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, speed);
}

void foreArmJointPitchUp(int speed) {
  Serial.println("Command: foreArmJointPitchUp");
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENB, speed);
}

void foreArmJointPitchDown(int speed) {
  Serial.println("Command: foreArmJointPitchUp");
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENB, speed);
}


// Motor control functions
void forward(int speed) {
  Serial.println("Command: Forward");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, speed); // PWM speed control
}

void reverse(int speed) {
  Serial.println("Command: Reverse");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, speed); // PWM speed control
}



void stopUpperArmJointMotor() {
  Serial.println("Command: Stop");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(ENA, LOW); // Disable motor
}

void stopForeArmJointMotor() {
  Serial.println("Command: Stop");
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(ENB, LOW); // Disable motor
}

void stopAllMotors() {
  stopUpperArmJointMotor();
  stopForeArmJointMotor();
}
