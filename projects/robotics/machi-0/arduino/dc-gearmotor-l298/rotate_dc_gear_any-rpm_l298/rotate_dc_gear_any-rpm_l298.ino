// L298 Motor Driver with Arduino Serial Control
// Command from Serial Monitor:
// 0 = Stop motor
// 1 = Forward for 1 second
// 2 = Reverse for 1 second

#include <IBusBM.h>

// ----- RC Input -----
IBusBM ibus;


// Pin definitions
const int ENA = 10;  // L298 ENA (Enable A)
const int IN1 = 8;   // L298 IN1
const int IN2 = 9;   // L298 IN2

// ----- Variables -----
char inChar = 0;             // Serial character input
bool commandSet = false;     // Track whether any command was activated
const int speedMin = 255;

void setup() {
  // Set motor control pins as output
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  // Start serial communication
  Serial.begin(115200);
  ibus.begin(Serial1);      // iBUS RX on Serial1 (Pin 19 on Mega)  
  Serial.println("Enter command: 0=Stop, 1=Forward 1s, 2=Reverse 1s");
}
// ===== MAIN LOOP =====
void loop() {
  commandSet = false;  // Reset command flag

  // --- Check Serial Command ---
  if (Serial.available()) {
    delay(10);
    inChar = (char)Serial.read();

    switch (inChar) {
      case '0': stopMotor();       break;
      case '1': forward(speedMin); break;
      case '2': reverse(speedMin); break;
    }

    commandSet = true;  // Serial input takes control
  }

  // --- RC Input Check (Priority Only If No Serial Command Issued) ---
  if (!commandSet) {
    int ch1Value = ibus.readChannel(0); // CH1 (Steering)
    int ch2Value = ibus.readChannel(1); // CH2 (Throttle)

    bool rcAction = false;

    if (ch2Value >= 1000 && ch2Value <= 1250) {
      reverse(speedMin);
      rcAction = true;
    } else if (ch2Value >= 1750 && ch2Value <= 2000) {
      forward(speedMin);
      rcAction = true;
    }

    // if (ch1Value >= 1000 && ch1Value <= 1450) {
    //   doLeftTurn();
    //   rcAction = true;
    // } else if (ch1Value >= 1550 && ch1Value <= 2000) {
    //   doRightTurn();
    //   rcAction = true;
    // }

    if (!rcAction) {
      stopMotor();
    }
  }

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

void stopMotor() {
  Serial.println("Command: Stop");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(ENA, LOW); // Disable motor
}
