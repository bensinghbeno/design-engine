#include <Wire.h>

#include <IBusBM.h>
#include <Cytron_SmartDriveDuo.h>

// ----- SmartDriveDuo Pin Definitions -----
#define IN1 4
#define AN1 5
#define AN2 6
#define IN2 7

Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);
const int speedMin = 50;
signed int speedLeft = 0;    // Final left motor speed
signed int speedRight = 0;   // Final right motor speed


#define AS5600_ADDR 0x36
#define ANGLE_HIGH  0x0E
#define ANGLE_LOW   0x0F

volatile long revCount = 0;
uint16_t lastRaw = 0;

void doAngleTracking()
{
  // ---- Continuous multi-turn tracking ----
  uint16_t raw = readRawAngle();
  int diff = raw - lastRaw;
  // Handle rollover (+ to – direction)
  if (diff > 2048)       revCount--;
  else if (diff < -2048) revCount++;
  lastRaw = raw;
}

void doForward() {
  int rampMapCount = 4000;
  for (int i = 0; i <= (rampMapCount); i++) {
    int rampSpeed = map(i, 0, rampMapCount, 0, speedMin); // Ramp speed from 0 to speedMin
    speedLeft = rampSpeed;
    speedRight = -rampSpeed;
    smartDriveDuo30.control(speedLeft, speedRight);

    doAngleTracking();

    delay(1); // Adjust delay for smoother ramping
  }
  Serial.println(":: FORWARD");
}

void doReverse() {
  speedLeft = speedMin;
  speedRight = -speedMin;
  smartDriveDuo30.control(speedLeft, speedRight);
  Serial.println(":: REVERSE");
}


void doStop() {
  speedLeft = 0;
  speedRight = 0;
  smartDriveDuo30.control(speedLeft, speedRight);  // <-- ADD THIS LINE
  smartDriveDuo30.control(speedLeft, speedRight);  
  Serial.println(":: STOP");
}



uint16_t readRawAngle() {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(ANGLE_HIGH);
  Wire.endTransmission(false);

  Wire.requestFrom(AS5600_ADDR, 2);
  uint8_t high = Wire.read();
  uint8_t low  = Wire.read();

  return ((high & 0x0F) << 8) | low;   // 12-bit angle (0–4095)
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // MDDS360
  pinMode(IN1, OUTPUT);
  pinMode(AN1, OUTPUT);
  pinMode(AN2, OUTPUT);
  pinMode(IN2, OUTPUT);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(AN1, 0);
  analogWrite(AN2, 0);

  //AS5600
  Wire.begin();
  Wire.setClock(400000);   // ✅ Set I2C to 400 kHz (fast mode)
  lastRaw = readRawAngle();
  Serial.println("== AS5600 DC Motor MDDS360 CLOSED LOOP ==");
}

void loop() {

  doAngleTracking();

  // ---- Check for serial request ----
  if (Serial.available()) {
    char command = Serial.read();   // Read received character
    if (command == 'd') {
      uint16_t raw = readRawAngle();
      float angle = raw * 360.0 / 4096.0;
      float totalDeg = revCount * 360.0 + angle;
      Serial.print("Revs: ");
      Serial.print(revCount);
      Serial.print("   Angle: ");
      Serial.print(angle, 2);
      Serial.print(" deg   Total: ");
      Serial.println(totalDeg, 2);
    }
    else if (command == 'f') {
      doForward();
      doStop();
    }
    
  }
}