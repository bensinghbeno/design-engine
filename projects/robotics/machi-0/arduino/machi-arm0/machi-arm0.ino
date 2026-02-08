#include <Cytron_SmartDriveDuo.h>

#include <IBusBM.h>

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>



// Right Elbow Pitch Servo on PCA9685
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();
#define SERVO_CHANNEL 0  // Using CH0 on PCA9685
#define SERVO_CHANNEL4 4  // Using CH0 on PCA9685
#define SERVOMIN 100     // Minimum pulse length out of 4096
#define SERVOMAX 500     // Maximum pulse length out of 4096
#define SERVOMID 300     // Maximum pulse length out of 4096
#define RAMPSTEP 10     
#define RAMPDELAY 1     
//

// Right Gripper Servo on PCA9685
#define GRIPPER_CHANNEL 4  // Using CH4 on PCA9685
#define R_GRIPPER_SERVOMIN 300     // Minimum pulse length out of 4096
#define R_GRIPPER_SERVOMAX 400     // Maximum pulse length out of 4096
#define R_GRIPPER_SERVOMID 300     // Maximum pulse length out of 4096
#define R_GRIPPER_RAMPSTEP 10     
#define R_GRIPPER_RAMPDELAY 1     

// State variables for non-blocking gripper control
bool gripperCloseActive = false;
bool gripperOpenActive = false;
int gripperPulse = SERVOMID; // Start at the middle position
unsigned long lastGripperUpdate = 0;
//



// ----- Cytron_SmartDriveDuo ArmUpperRightMotor -----
#define INAUR1 4 
#define ANAUR1 5
#define ANAUR2 6
#define INAUR2 7

signed int speedLeft = 0;  
signed int speedRight = 0;   
const int BASEJ_YAW_SPEED_MIN = 150;
const int BASEJ_ROLL_SPEED_MIN = 100;
bool enableRightUpperArmPitch = false;
bool isRightHandOpen = false; // Tracks whether the hand is open

bool enableFwdReverseS1 = false;
bool enableFwdReverseS2 = false;


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

const int ENA = 10;  // Motor A enable (already used)
const int IN1 = 8;   // Motor A IN1 (already used)
const int IN2 = 9;   // Motor A IN2 (already used)

const int ENB = 13;  // Motor B enable (PWM)
const int IN3 = 11;  // Motor B IN3
const int IN4 = 12;  // Motor B IN4

// ----- Variables -----
char inChar = 0;             // Serial character input
bool commandSet = false;     // Track whether any command was activated
const int rcThrottleDelay  = 1000; // ms

// State variables for non-blocking elbow pitch control
bool elbowPitchUpActive = false;
bool elbowPitchDownActive = false;
int elbowPulse = SERVOMID; // Start at the middle position
unsigned long lastElbowUpdate = 0;



// void setup() {

//   allMotors_Stop();

//   //Set motor control pins as output
//   pinMode(ENA, OUTPUT);
//   pinMode(IN1, OUTPUT);
//   pinMode(IN2, OUTPUT);
//   pinMode(ENB, OUTPUT);
//   pinMode(IN3, OUTPUT);
//   pinMode(IN4, OUTPUT);

//   pwm.begin();
//   pwm.setPWMFreq(50); 
  

//   // Start serial communication
//   Serial.begin(115200);
//   ibus.begin(Serial1);      // iBUS RX on Serial1 (Pin 19 on Mega)  
//   Serial.println("Enter command: 0=Stop, 1=Forward 1s, 2=Reverse 1s");

//   //Init Motors
//   elbowPitchMidPos();
//   rightGripperMidPos();
// }

void setup() {
  Serial.begin(115200);
  delay(1000); // Give you time to open the monitor
  Serial.println("--- System Booting ---");



  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);




  Serial.println("Initializing PCA9685...");
  pwm.begin();
  pwm.setPWMFreq(50); 
  
  Serial.println("Initializing iBus...");
  ibus.begin(Serial1);      

  allMotors_Stop();
  Serial.println("Motors Stopped...");
  Serial.println("Setting Initial Positions...");
  elbowPitchMidPos();
  rightGripperMidPos();

 
  Serial.println("Setup Complete! Enter command: 0=Stop");
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

    if( (!enableFwdReverseS1) && (!enableFwdReverseS2) && (ch3Value >= 1900) ) 
    {
      enableFwdReverseS1 =  true;
      rcAction = true;
    } else if( (enableFwdReverseS1) && (!enableFwdReverseS2) && (ch3Value <= 1700) && (ch3Value >= 1300)) {
      enableFwdReverseS2 =  true;
      rcAction = true;
    } else if ( (enableFwdReverseS1) && (enableFwdReverseS2) && (ch3Value >= 1950) && (ch3Value <= 2000)){
      rightBaseJointRollUp(BASEJ_ROLL_SPEED_MIN);      
      rcAction = true;
    } else if ( (enableFwdReverseS1) && (enableFwdReverseS2) && (ch3Value >= 1000) && (ch3Value <= 1050)){
      rightBaseJointRollDown(BASEJ_ROLL_SPEED_MIN);      
      rcAction = true;                         
    } else if ( (enableFwdReverseS1) && (enableFwdReverseS2) && (ch4Value >= 1000) && (ch4Value <= 1200)){
      rightBaseJointYawLeft(BASEJ_YAW_SPEED_MIN);
      rcAction = true;
    } else if ( (enableFwdReverseS1) && (enableFwdReverseS2) && (ch4Value >= 1800) && (ch4Value <= 2000)){
      rightBaseJointYawRight(BASEJ_YAW_SPEED_MIN);
      rcAction = true;                           
    } else if (ch2Value >= 1750 && ch2Value <= 2000) {
      elbowPitchUp();
      rcAction = true;
    } else if (ch2Value >= 1000 && ch2Value <= 1250) {
      elbowPitchDown();
      rcAction = true;
    } /*else if (ch7Value >= 1300 && ch7Value <= 2000) {
      rcAction = true;
      gripperClose();
    } else if (ch7Value >= 1000 && ch7Value < 1300) {
      rcAction = true;
      gripperOpen();
    }  */
    //else if (ch2Value >= 1750 && ch2Value <= 2000) {
    //   foreArmRight_PitchUp();
    //   rcAction = true;
    // } else if ((enableRightUpperArmPitch) && (ch3Value <= 1100 )){
    //   enableRightUpperArmPitch = true;
    //   upperArmRight_PitchDown();
    //   rcAction = true;
    // } else if ((enableRightUpperArmPitch) && (ch3Value >= 1900 )){
    //   enableRightUpperArmPitch = true;
    //   upperArmRight_PitchUp();
    //   rcAction = true;
    // } else if ((enableRightUpperArmPitch == false) && (ch3Value >= 1300 && ch3Value <= 1700)) {
    //   enableRightUpperArmPitch = true;
    // } else if (ch5Value >= 1750 && ch5Value <= 2000) {
    //   rightHand_Close();
    //   rcAction = true;
    // } else if (ch5Value >= 1000 && ch5Value <= 1250) {
    //   rightHand_Open();
    //   rcAction = true;
    // }

    if (!rcAction) {
      allMotors_Stop();
    }
  }

  // Call the non-blocking elbow pitch functions
  elbowPitchUpNonBlocking();
  elbowPitchDownNonBlocking();

  // Call the non-blocking gripper functions
  gripperCloseNonBlocking();
  gripperOpenNonBlocking();
}


void elbowPitchUp()
{
  elbowPitchUpActive = true;
  Serial.println("Starting Elbow Pitch Up");
}

void elbowPitchDown()
{
  elbowPitchDownActive = true;
  Serial.println("Starting Elbow Pitch Down");
}

void elbowPitchUpNonBlocking() {
  if (elbowPitchUpActive) {
    unsigned long currentMillis = millis();
    if (currentMillis - lastElbowUpdate >= RAMPDELAY) {
      lastElbowUpdate = currentMillis;

      // Increment the pulse width
      if (elbowPulse <= SERVOMAX) {
        pwm.setPWM(SERVO_CHANNEL, 0, elbowPulse);
        elbowPulse += RAMPSTEP; // Increment pulse
      } else {
        // Stop the movement when the maximum is reached
        elbowPitchUpActive = false;
        Serial.println("Elbow Pitch Up Complete");
      }
    }
  }
}

void elbowPitchDownNonBlocking() {
  if (elbowPitchDownActive) {
    unsigned long currentMillis = millis();
    if (currentMillis - lastElbowUpdate >= RAMPDELAY) {
      lastElbowUpdate = currentMillis;

      // Decrement the pulse width
      if (elbowPulse >= SERVOMIN) {
        pwm.setPWM(SERVO_CHANNEL, 0, elbowPulse);
        elbowPulse -= RAMPSTEP; // Decrement pulse
      } else {
        // Stop the movement when the minimum is reached
        elbowPitchDownActive = false;
        Serial.println("Elbow Pitch Down Complete");
      }
    }
  }
}


void elbowPitchMidPos()
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

void rightGripperMidPos()
{
  // Stop servo
  Serial.println("Min Pos Stopping");
  pwm.setPWM(GRIPPER_CHANNEL, 0, R_GRIPPER_SERVOMID);
  delay(100);
  pwm.setPWM(GRIPPER_CHANNEL, 0, R_GRIPPER_SERVOMID);
  delay(100);
  pwm.setPWM(GRIPPER_CHANNEL, 0, R_GRIPPER_SERVOMID);
  pwm.setPWM(GRIPPER_CHANNEL, 0, 0); // Stop position
  delay(100); // Hold for 2 seconds
}


void elbowPitchStop()
{
      // Stop servo
    Serial.println("Stopping stopElbowPitchServo");
    pwm.setPWM(SERVO_CHANNEL, 0, 0); // Stop position
    elbowPitchUpActive = false;
    elbowPitchDownActive = false;}


void allMotors_Stop() {
  upperArmRight_PitchStop();
  upperArmRight_RollStop();
  moveForwardReverse_Stop();
  elbowPitchStop();
}


void rightBaseJointRollUp(int speed) {
  Serial.println("Command: rightBaseJointRollUp");

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, speed);    
}

void rightBaseJointRollDown(int speed) {
  Serial.println("Command: rightBaseJointRollDown");

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, speed);
}

void rightBaseJointYawLeft(int speed) {
  Serial.println("Command: rightBaseJointYawLeft");

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENB, speed);
}

void rightBaseJointYawRight(int speed) {
  Serial.println("Command: rightBaseJointYawRight");

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENB, speed);
}

void rightHand_Open() 
{
  if (isRightHandOpen) {
    Serial.println(":: rightHand_Open - Already Open");
    return; // Do nothing if the hand is already open
  }

  Serial.println(":: rightHand_Open");

  // Gradually move the servo to the open position
  for (int pulse = SERVOMIN; pulse <= SERVOMAX; pulse += 10) { // Increment in small steps
    pwm.setPWM(SERVO_CHANNEL, 0, pulse);
    delay(20); // Small delay for smooth movement
  }

  // Mark the hand as open
  isRightHandOpen = true;
}

void rightHand_Close() 
{
  if (!isRightHandOpen) {
    Serial.println(":: rightHand_Close - Already Closed");
    return; // Do nothing if the hand is already closed
  }

  Serial.println(":: rightHand_Close");

  // Gradually move the servo to the closed position
  for (int pulse = SERVOMAX; pulse >= SERVOMIN; pulse -= 10) { // Decrement in small steps
    pwm.setPWM(SERVO_CHANNEL, 0, pulse);
    delay(20); // Small delay for smooth movement
  }

  // Mark the hand as closed
  isRightHandOpen = false;
}


void moveLeft(int speed) {
  Serial.println("Command: moveLeft");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, speed);  

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENB, speed);  
}

void moveRight(int speed) {
  Serial.println("Command: moveRight");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, speed);  

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENB, speed);  
}

void moveForwardReverse_Stop() {
  Serial.println("Command: moveForwardReverse_Stop");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 0);  

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  analogWrite(ENB, 0);    
}


void upperArmRight_PitchStop() 
{
  smartDriveDuo30.control(0, 0);  
  Serial.println(":: uppertArmRight_Stop");
}

void upperArmRight_RollStop() 
{
  Serial.println("Command: upperArmRight_RollStop");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 0);
}


void upperArmRight_PitchUp()
{
  speedLeft = BASEJ_ROLL_SPEED_MIN;
  speedRight = -BASEJ_ROLL_SPEED_MIN;
  smartDriveDuo30.control(speedLeft, 0);  
  Serial.println(":: upperRightArm_PitchDown");
}

void upperArmRight_PitchDown()
{
  speedLeft = -BASEJ_ROLL_SPEED_MIN;
  speedRight = BASEJ_ROLL_SPEED_MIN;
  smartDriveDuo30.control(speedLeft, 0); 
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

// Function to start closing the gripper
void gripperOpen() {
  gripperOpenActive = true;
  Serial.println("Starting Gripper Open");
}

// Non-blocking function to open the gripper
void gripperOpenNonBlocking() {
  if (gripperOpenActive) {
    unsigned long currentMillis = millis();
    if (currentMillis - lastGripperUpdate >= R_GRIPPER_RAMPDELAY) {
      lastGripperUpdate = currentMillis;

      // Increment the pulse width
      if (gripperPulse <= R_GRIPPER_SERVOMIN) {
        pwm.setPWM(GRIPPER_CHANNEL, 0, gripperPulse);
        gripperPulse += R_GRIPPER_RAMPSTEP; // Increment pulse
      } else {
        // Stop the movement when the maximum is reached
        gripperOpenActive = false;
        Serial.println("Gripper Open Complete");
      }
    }
  }
}

// Function to start opening the gripper
void gripperClose() {
  gripperCloseActive = true;
  Serial.println("Starting Gripper Close");
}

// Non-blocking function to close the gripper
void gripperCloseNonBlocking() {
  if (gripperCloseActive) {
    unsigned long currentMillis = millis();
    if (currentMillis - lastGripperUpdate >= R_GRIPPER_RAMPDELAY) {
      lastGripperUpdate = currentMillis;

      // Decrement the pulse width
      if (gripperPulse >= R_GRIPPER_SERVOMAX) {
        pwm.setPWM(GRIPPER_CHANNEL, 0, gripperPulse);
        gripperPulse -= R_GRIPPER_RAMPSTEP; // Decrement pulse
      } else {
        // Stop the movement when the minimum is reached
        gripperCloseActive = false;
        Serial.println("Gripper Close Complete");
      }
    }
  }
}




