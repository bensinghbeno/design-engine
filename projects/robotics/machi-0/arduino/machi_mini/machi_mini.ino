#include <Arduino.h>
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

// ----- Variables -----
char inChar = 0;             // Serial character input
bool commandSet = false;     // Track whether any command was activated
const int rcThrottleDelay  = 1000; // ms

// ----- L298 Pin Definitions -----
const int ENA = 10;  // Motor A enable (already used)
const int IN1 = 8;   // Motor A IN1 (already used)
const int IN2 = 9;   // Motor A IN2 (already used)

const int ENB = 13;  // Motor B enable (PWM)
const int IN3 = 11;  // Motor B IN3
const int IN4 = 12;  // Motor B IN4

int g_drive_speed = 150;
int g_drive_turn_speed = 255;

void right_Drive_Forward(const int speed)
{
  Serial.println("Command: right_Drive_Forward");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, speed);
}

void right_Drive_Reverse(const int speed)
{
  Serial.println("Command: right_Drive_Reverse");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, speed);
}

void left_Drive_Forward(const int speed)
{
  Serial.println("Command: left_Drive_Forward");
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENB, speed);
}

void left_Drive_Reverse(const int speed)
{
  Serial.println("Command: left_Drive_Reverse");
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENB, speed);
}

void right_Drive_Stop()
{
  Serial.println("Command: right_Drive_Stop");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 0);
}

void left_Drive_Stop()
{
  Serial.println("Command: left_Drive_Stop");
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  analogWrite(ENB, 0);
}

void doForward() {
  Serial.println("::  FORWARD");
  right_Drive_Forward(g_drive_speed);
  left_Drive_Forward(g_drive_speed);
}

void doReverse() {
  Serial.println("::  REVERSE");
  right_Drive_Reverse(g_drive_speed);
  left_Drive_Reverse(g_drive_speed);
}
void doLeftTurn() {
  Serial.println(":: LEFT TURN");
  right_Drive_Reverse(g_drive_turn_speed);
  left_Drive_Forward(g_drive_turn_speed);
}

void doRightTurn() {
  Serial.println(":: RIGHT TURN");
  right_Drive_Forward(g_drive_turn_speed);
  left_Drive_Reverse(g_drive_turn_speed);
}


void doStopAll() {
  right_Drive_Stop();
  left_Drive_Stop();
  Serial.println("doStopAll :: STOP");
}

// ===== SETUP =====
void setup() {
  delay(200);

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  Serial.begin(115200);     // Serial monitor
  delay(200); // Give you time to open the monitor
  Serial.println("--- SYSTEM INIT ---");

  Serial.println("Initializing iBus...");
  ibus.begin(Serial1);      

  doStopAll();
  Serial.println("====== ARDUINO MEGA: SYSTEM INIT COMPLETE =======");
}

// ===== MAIN LOOP =====
void loop()
{
  // Scan iBus channels
  ch1Value = ibus.readChannel(0);
  Serial.print("Ch1 ");
  Serial.print(ch1Value);
  Serial.print(" | ");

  ch2Value = ibus.readChannel(1);
  Serial.print("Ch2 ");
  Serial.print(ch2Value);
  Serial.print(" | ");

  ch3Value = ibus.readChannel(2);
  Serial.print("Ch3 ");
  Serial.print(ch3Value);
  Serial.print(" | ");

  ch4Value = ibus.readChannel(3);
  Serial.print("Ch4 ");
  Serial.print(ch4Value);
  Serial.print(" | ");

  Serial.print("Ch5 ");
  ch5Value = ibus.readChannel(4);
  Serial.print(ch5Value);
  Serial.print(" | ");

  ch6Value = ibus.readChannel(5);
  Serial.print("Ch6 ");
  Serial.print(ch6Value);
  Serial.print(" | ");

  ch7Value = ibus.readChannel(6);
  Serial.print("Ch7 ");
  Serial.print(ch7Value);
  Serial.print(" | ");

  ch8Value = ibus.readChannel(7);
  Serial.print("Ch8 ");
  Serial.print(ch8Value);
  Serial.print(" | ");

  Serial.println();
  delay(10);

  if (ch2Value >= 1000 && ch2Value <= 1250) {
    doReverse();
  } else if (ch2Value >= 1750 && ch2Value <= 2000) {
    doForward();
  } else if (ch1Value <= 1450) {
    doRightTurn();
  } else if (ch1Value >= 1550) {
    doLeftTurn();
  }
  else
  {
    doStopAll();
  }
}
