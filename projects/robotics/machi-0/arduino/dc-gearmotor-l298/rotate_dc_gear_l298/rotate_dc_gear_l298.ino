/*
🔌 Arduino Mega ↔ L298N Connections
L298N Pin	Connect to Arduino Mega Pin	Purpose
IN1	Digital Pin 8	Motor direction control input 1
IN2	Digital Pin 9	Motor direction control input 2
ENA (Enable A)	PWM Pin 10	Motor speed control (PWM)
GND	Arduino GND	Common ground
5V	Leave jumper ON (powered from motor 12V supply regulator)	Logic power (via onboard regulator)
VMS (Motor supply)	Connect to 12V external power source	Motor power supply

Arduino ↔ Motor+Encoder Connections:
Motor Encoder Wire	Arduino Mega Pin	Purpose
Encoder VCC (Blue)	Arduino 5V	Encoder power
Encoder GND (Gray)	Arduino GND	Encoder ground (common GND)
Encoder Channel A (Yellow)	Digital Pin 2 (interrupt 0)	Encoder pulse A input
Encoder Channel B (White)	Digital Pin 3	Encoder pulse B input

*/

volatile long encoderCount = 0;
int targetCount = 0;

const int motorIn1 = 8; //test
const int motorIn2 = 9;
const int motorPWM = 10;

const int encoderPinA = 2;  // Interrupt 0
const int encoderPinB = 3;

void setup() {

  Serial.begin(115200);

  pinMode(motorIn1, OUTPUT);
  pinMode(motorIn2, OUTPUT);
  pinMode(motorPWM, OUTPUT);

  pinMode(encoderPinA, INPUT);
  pinMode(encoderPinB, INPUT);

  attachInterrupt(digitalPinToInterrupt(encoderPinA), updateEncoder, CHANGE);

  Serial.print("Setup() : ");

  stopMotor();
}

void loop() {
  if (Serial.available()) {
    char command = Serial.read();

    if (!command)
    {
      Serial.print("Received command: ");
      Serial.println(command);
    }

    switch (command) {
      case '0':
        stopMotor();
        break;

      case '1':
        rotateBen();  // Clockwise
        break;

      case '2':
        rotateClockwiseUntilDecrement();
        break;

      case '3':
        applyReverseBrake();
        break;        

      case '4':
        rotateSmoothClockwiseFor1sSlow();
        break;

      case '5':
        displayEncoderCount();
        break;
    }
  }
}

void rotateClockwiseUntilDecrement() {
  Serial.print("rotateClockwiseUntilDecrement() : ");

  long startCount = encoderCount;
  Serial.print("Starting encoder count: ");
  Serial.println(startCount);

  digitalWrite(motorIn1, HIGH);
  digitalWrite(motorIn2, LOW);
  analogWrite(motorPWM, 200);
  Serial.println("Motor running clockwise at PWM 200.");

  while ((startCount - encoderCount) < 1000) {
    // Optionally, add a small delay for stability
    // delay(1);
  }

  applyReverseBrake();
  Serial.print("Stopped. Encoder decremented by: ");
  Serial.println(startCount - encoderCount);
}

void applyReverseBrake() {
  Serial.print("applyReverseBrake() : ");

  long startCount = encoderCount;
  Serial.print("Starting encoder count: ");
  Serial.println(startCount);

  digitalWrite(motorIn1, LOW);
  digitalWrite(motorIn2, HIGH);
  analogWrite(motorPWM, 200);
  Serial.println("Motor Braking anti-clockwise at PWM 200.");

  Serial.println("------ Motor running ------");
  unsigned long startTime = millis();
  while (millis() - startTime < 75) {
  }
  Serial.println("------- Timeout ------------ ");

  stopMotor();

  Serial.print("Motor Braked : ");
}

void rotateBen()
{
  Serial.print("RotateBen() : ");

  displayEncoderCount();

  rotateSmoothClockwiseFor1sSlow();

  displayEncoderCount();

}

void rotateSmoothClockwiseFor1sSlow() {
  Serial.println("rotateSmoothClockwiseFor1sSlow() : ");
  digitalWrite(motorIn1, HIGH);
  digitalWrite(motorIn2, LOW);
  analogWrite(motorPWM, 80);
  Serial.println("------ Motor running ------");
  unsigned long startTime = millis();
  while (millis() - startTime < 500) {
  }
  Serial.println("------- Timeout ------------ ");

  stopMotor();
}

void displayEncoderCount()
{
  Serial.print("Encoder count = ");
  Serial.println(encoderCount);
}



void updateEncoder() {
  bool A = digitalRead(encoderPinA);
  bool B = digitalRead(encoderPinB);

  if (A == B) {
    encoderCount++;
  } else {
    encoderCount--;
  }

  // Log encoder count every 10 pulses for less serial spam
  static long lastLogged = 0;
  if (abs(encoderCount - lastLogged) >= 10) {
    Serial.print("-- Encoder count = ");
    Serial.println(encoderCount);
    lastLogged = encoderCount;
  }
}




void rotate90(bool clockwise) {
  encoderCount = 0;
  targetCount = 150; // Adjust this based on your gear ratio

  Serial.print("Target encoder count: ");
  Serial.println(targetCount);

  if (clockwise) {
    digitalWrite(motorIn1, HIGH);
    digitalWrite(motorIn2, LOW);
    Serial.println("Direction: Clockwise");
  } else {
    digitalWrite(motorIn1, LOW);
    digitalWrite(motorIn2, HIGH);
    Serial.println("Direction: Counter-clockwise");
  }

  analogWrite(motorPWM, 180);  // Adjust speed as needed
  Serial.println("Motor started.");

  while (abs(encoderCount) < targetCount) {
    // Wait until target count reached
    // Optionally log progress
    // Serial.print("Current encoder count: ");
    // Serial.println(encoderCount);
    // delay(10); // Uncomment for slower logging
  }

  stopMotor();
  Serial.println("Target reached. Motor stopped.");
}

void stopMotor() {
  analogWrite(motorPWM, 0);
  digitalWrite(motorIn1, LOW);
  digitalWrite(motorIn2, LOW);
  Serial.println("StopMotor() :");
}

