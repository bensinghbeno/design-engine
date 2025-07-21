/* 
 * This example shows how to control MDDS30 in PWM mode with Arduino.
 * Set MDDS30 input mode to 0b10110100
 * Open Serial Monitor, set baudrate to 9600bps and "No line ending".
 * Send 0: Left motor stops
 *      1: Left motor rotates CW with half speed
 *      2: Left motor rotates CW with full speed
 *      3: Left motor rotates CCW with half speed
 *      4: Left motor rotates CCW with full speed
 *      5: Right motor stops
 *      6: Right motor rotates CW with half speed
 *      7: Right motor rotates CW with full speed
 *      8: Right motor rotates CCW with half speed
 *      9: Right motor rotates CCW with full speed
 * 
 * Note: This example also compatible with MDDS10 and MDDS60
 *
 * Hardware Connection:
 *   Arduino Uno    MDDS30
 *   GND ---------- GND
 *   4 ------------ IN1
 *   5 ------------ AN1
 *   6 ------------ AN2
 *   7 ------------ IN2
 *
 * Related Products:
 * - SmartDriveDuo-30: http://www.cytron.com.my/P-MDDS60
 * - CT UNO: http://www.cytron.com.my/p-ct-uno
 * - DC Brush Motors: http://www.cytron.com.my/c-84-dc-motor
 * - LiPo Battery: http://www.cytron.com.my/c-87-power/c-97-lipo-rechargeable-battery-and-charger
 * - Male to Male Jumper: https://www.cytron.com.my/p-wr-jw-mm65
 *
 * URL: http://www.cytron.com.my
 */

#include <Cytron_SmartDriveDuo.h>
#define IN1 4 // Arduino pin 4 is connected to MDDS30 pin IN1.
#define AN1 5 // Arduino pin 5 is connected to MDDS30 pin AN1.
#define AN2 6 // Arduino pin 6 is connected to MDDS30 pin AN2.
#define IN2 7 // Arduino pin 7 is connected to MDDS30 pin IN2.
Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);

char inChar;
signed int speedLeft, speedRight;

void setup() {
  // Set pinMode before doing anything else
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(AN1, OUTPUT);
  pinMode(AN2, OUTPUT);
  
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(AN1, 0);
  analogWrite(AN2, 0);
  
  digitalWrite(13, LOW); // Status LED
  
  Serial.begin(9600);  
  delay(2000); // Optional delay
  Serial.println("====== ARDUINO MEGA : INIT SETUP COMPLETED =======");

}


void loop()
{
  if (Serial.available()) {
    delay(100);
    inChar = (char)Serial.read();

    if (inChar == '0') {
      speedLeft = 0;
      speedRight = 0;
      Serial.println(":: Stop");
    }
    else if (inChar == '1') {
      speedLeft = 50;
      speedRight = -50;
      Serial.println(":: Reverse");
    }
    else if (inChar == '2') {
      speedLeft = -50;
      speedRight = 50;
      Serial.println(":: Forward");
    }
    else if (inChar == '3') {
      speedLeft = 50;
      speedRight = 50;
      Serial.println(":: Turn Left");
    }
    else if (inChar == '4') {
      speedLeft = -50;
      speedRight = -50;  
      Serial.println(":: Turn Right");
    }

    smartDriveDuo30.control(speedLeft, speedRight);
  }
}

