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
char inChar;
int ch1Value;
int ch2Value;
int ch3Value;
int ch4Value;
int ch5Value;
int ch6Value;
int ch7Value;
int ch8Value;

signed int speedLeft = 0;    // Final left motor speed
signed int speedRight = 0;   // Final right motor speed
bool commandSet = false;     // Track whether any command was activated
const int speedMin = 255;



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
      delay(100);

    Serial.print("Ch1 ");
    Serial.print(ch1Value);
    Serial.print(" | ");

    Serial.print("Ch2 ");
    Serial.print(ch2Value);
    Serial.print(" | ");


    delay(10);

}
