// ----- L298 Pin Definitions -----
const int ENA = 10;  // Motor A enable (already used)
const int IN1 = 8;   // Motor A IN1 (already used)
const int IN2 = 9;   // Motor A IN2 (already used)

const int ENB = 13;  // Motor B enable (PWM)
const int IN3 = 11;  // Motor B IN3
const int IN4 = 12;  // Motor B IN4

int g_drive_speed = 150;

// Declare inChar as a global variable
char inChar;


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
  Serial.println("Command: left_Drive_Stop");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 0);
}

void left_Drive_Stop() 
{
  Serial.println("Command: left_Drive_Stop");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(ENB, 0);
}



void doLongForward() {
  Serial.println(":: LONG FORWARD");

  right_Drive_Forward(g_drive_speed);
  left_Drive_Forward(g_drive_speed);
  delay(1000);
  doStopAll();
}

void doLongReverse() {
  Serial.println(":: LONG REVERSE");

  right_Drive_Reverse(g_drive_speed);
  left_Drive_Reverse(g_drive_speed);
  delay(1000);
  doStopAll();
}

void doStopAll() {
  right_Drive_Stop();
  left_Drive_Stop();

  Serial.println("doStopAll :: STOP");
}

// ===== SETUP =====
void setup() {
  delay(200); // Give you time to open the monitor

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);


  Serial.begin(115200);     // Serial monitor
  delay(200); // Give you time to open the monitor
  Serial.println("--- SYSTEM INIT ---");


  doStopAll();
  Serial.println("====== ARDUINO MEGA: SYSTEM INIT COMPLETE =======");
}

// ===== MAIN LOOP =====
void loop()
{

  // --- Check Serial Command ---
  if (Serial.available())
   {
    delay(10);
    inChar = (char)Serial.read();

      switch (inChar) 
      {
        case '0': doStopAll();break;
        case '1': doLongForward(); break;
        case '2': doLongReverse(); break;
      }
    }
}
