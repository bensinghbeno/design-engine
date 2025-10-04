#include <Cytron_SmartDriveDuo.h>

#include <IBusBM.h>

// ----- Cytron_SmartDriveDuo ArmUpperRightMotor -----
#define INAUR1 4
#define ANAUR1 5
#define ANAUR2 6
#define INAUR2 7

signed int speedLeft = 0;  
signed int speedRight = 0;   
const int speedMin = 255;

Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, INAUR1, INAUR2, ANAUR1, ANAUR2);

// ------ //


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

// const int ENB = 13;  // Motor B enable (PWM)
// const int IN3 = 11;  // Motor B IN3
// const int IN4 = 12;  // Motor B IN4

// ----- Variables -----
char inChar = 0;             // Serial character input
bool commandSet = false;     // Track whether any command was activated
const int rcThrottleDelay  = 1000; // ms

void setup() {

  allMotors_Stop();

  //Set motor control pins as output
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  // pinMode(ENB, OUTPUT);
  // pinMode(IN3, OUTPUT);
  // pinMode(IN4, OUTPUT);
  

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
      case '0': allMotors_Stop(); break;
      //case '1': forward(speedMin); break;
      //case '2': reverse(speedMin); break;
    }

    commandSet = true;  // Serial input takes control
  }

  // --- RC Input Check (Priority Only If No Serial Command Issued) ---
  if (!commandSet) {

    bool rcAction = false;

    if (ch1Value >= 1000 && ch1Value <= 1250) {
      upperArmRight_RollLeft(speedMin);
      rcAction = true;
    } else if (ch1Value >= 1750 && ch1Value <= 2000) {
      upperArmRight_RollRight(speedMin);
      rcAction = true;
    } else if (ch2Value >= 1000 && ch2Value <= 1250) {
      upperArmRight_PitchDown();
      rcAction = true;
    } else if (ch2Value >= 1750 && ch2Value <= 2000) {
      upperArmRight_PitchUp();
      rcAction = true;
    }


    if (!rcAction) {
      allMotors_Stop();
    }
  }

}

void allMotors_Stop() {
  upperArmRight_PitchStop();
  upperArmRight_RollStop();

}

void upperArmRight_PitchStop() 
{
  smartDriveDuo30.control(0, 0);  // <-- ADD THIS LINE
  Serial.println(":: uppertArmRight_Stop");
}

void upperArmRight_RollStop() 
{
  Serial.println("Command: upperArmRight_RollStop");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 0);
}

void upperArmRight_Stop() 
{
  smartDriveDuo30.control(0, 0);  // <-- ADD THIS LINE
  Serial.println(":: uppertArmRight_Stop");
}

void upperArmRight_PitchUp()
{
  speedLeft = speedMin;
  speedRight = -speedMin;
  smartDriveDuo30.control(speedLeft, speedRight);  // <-- ADD THIS LINE
  Serial.println(":: upperRightArm_PitchDown");
}

void upperArmRight_PitchDown()
{
  speedLeft = -speedMin;
  speedRight = speedMin;
  smartDriveDuo30.control(speedLeft, speedRight);  // <-- ADD THIS LINE
  Serial.println(":: upperRightArm_PitchDown");
}


void upperArmRight_RollLeft(int speed) {
  Serial.println("Command: upperArmRight_RollLeft");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, speed);
}

void upperArmRight_RollRight(int speed) {
  Serial.println("Command: upperArmRight_RollRight");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, speed);
}

/*


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




void stopForeArmJointMotor() {
  Serial.println("Command: Stop");
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(ENB, LOW); // Disable motor
}
*/


