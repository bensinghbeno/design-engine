#include <Wire.h>

#include <IBusBM.h>
#include <Cytron_SmartDriveDuo.h>

// ----- SmartDriveDuo Pin Definitions -----
#define IN1 4
#define AN1 5
#define AN2 6
#define IN2 7

#define BUFFER_DIFF_POSE 500

Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);
const int speedMin = 50;
signed int speedLeft = 0;    // Final left motor speed
signed int speedRight = 0;   // Final right motor speed


#define AS5600_ADDR 0x36
#define ANGLE_HIGH  0x0E
#define ANGLE_LOW   0x0F

volatile long revCount = 0;
uint16_t lastRaw = 0;

void doAngleTracking() {
    // ---- Continuous multi-turn tracking ----
    uint16_t raw = readRawAngle();
    int diff = raw - lastRaw;
    // Handle rollover (+ to – direction)
    if (diff > 2048) {
        revCount--;
    } else if (diff < -2048) {
        revCount++;
    }
    lastRaw = raw;
}

void setTarget(int targetPos) {
    Serial.println("setTarget() :: ");

    while (true) {
        doAngleTracking();
        int latPos = abs(targetPos);
        float lcPos = getCurrentPos();
        float lacPos = abs(lcPos);
        int ldiffPos = latPos - lacPos;
        int ladiffPos = abs(ldiffPos);

        Serial.print("atPos  : ");
        Serial.print(latPos);
        Serial.print(", acPos  : ");
        Serial.println(lacPos);  
        Serial.print(", adiffPos  : ");
        Serial.println(ladiffPos);          


        if (ladiffPos <= BUFFER_DIFF_POSE) {
            doAngleTracking();
            Serial.println("=== F-target within Buffer, Will Stop Motor ===");
            doStop();
        } 
        else if (ladiffPos > BUFFER_DIFF_POSE) 
        {
         doAngleTracking();
            
            if (latPos > lacPos) 
            {
              Serial.println("=== FORWARD CONTROL ===");
              if (doForwardPose(targetPos)) 
              {
                    Serial.println("=== F-target Reached, Will Stop Motor ===");
                    doAngleTracking();
                    doStop();
              }
            }
            else if(latPos < lacPos) 
            {
              Serial.println("=== REVERSE CONTROL ===");
              if (doReversePose(targetPos)) 
              {
                    Serial.println("=== R-target Reached, Will Stop Motor ===");
                    doAngleTracking();
                    doStop();
              }
            }

        } else {
            doStop();
            doAngleTracking();
        }
    }
}

bool doForwardPose(int fPos) {
    Serial.print("doForwardPose() : ");
    Serial.println(fPos);
    int rampMapCount = 4000;
    bool quitF = false;
    for (int i = 0; ((!quitF) && (i <= (rampMapCount))); i++) {
        int rampSpeed = map(i, 0, rampMapCount, 0, speedMin); // Ramp speed from 0 to speedMin
        speedLeft = rampSpeed;
        speedRight = -rampSpeed;
        smartDriveDuo30.control(speedLeft, speedRight);

        doAngleTracking();

        delay(1); // Adjust delay for smoother ramping

        float cPos = getCurrentPos();
        if (fPos > cPos) {
            quitF = true;
            return true;
        } else {
            Serial.print("Continue doForwardPose(), Current Pos : ");
            Serial.println(cPos);
        }
    }
    return false;
}

bool doReversePose(int rPos) {
    Serial.print("doReversePose() : ");
    Serial.println(rPos);
    int rampMapCount = 4000;
    bool quitR = false;
    for (int i = 0; ((!quitR) && (i <= (rampMapCount))); i++) {
        int rampSpeed = map(i, 0, rampMapCount, 0, speedMin); // Ramp speed from 0 to speedMin
        speedLeft = -rampSpeed;
        speedRight = rampSpeed;
        smartDriveDuo30.control(speedLeft, speedRight);

        doAngleTracking();

        delay(1); // Adjust delay for smoother ramping

        float cPos = getCurrentPos();
        if (rPos < cPos) {
            quitR = true;
            return true;
        } else {
            Serial.print("Continue doReversePose(), Current Pos : ");
            Serial.println(cPos);
        }
    }
    return false;
}

float getCurrentPos() {
    uint16_t raw = readRawAngle();
    float angle = raw * 360.0 / 4096.0;
    float totalDeg = revCount * 360.0 + angle;
    return totalDeg;
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
    Serial.println("doStop() Motor :: ");
}

uint16_t readRawAngle() {
    Wire.beginTransmission(AS5600_ADDR);
    Wire.write(ANGLE_HIGH);
    Wire.endTransmission(false);

    Wire.requestFrom(AS5600_ADDR, 2);
    uint8_t high = Wire.read();
    uint8_t low = Wire.read();

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

    // ---- Check if we have a full command line ----
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');  // Read until newline
        input.trim();  // Remove spaces or carriage return

        if (input.length() == 0) {
            return; // ignore empty input
        }

        // ---- Check if it's numeric ----
        if ((input.charAt(0) >= '0' && input.charAt(0) <= '9') || input.charAt(0) == '-') {
            int number = input.toInt();
            if (number >= -4000 && number <= 1000) {
                Serial.print("Received number: ");
                Serial.println(number);
                setTarget(number);
            } else {
                Serial.println("Number out of range :: ");
            }
        }

        // ---- Single character command ----
        else if (input == "d") {
            uint16_t raw = readRawAngle();
            float angle = raw * 360.0 / 4096.0;
            float totalDeg = revCount * 360.0 + angle;
            Serial.print("Revs: ");
            Serial.print(revCount);
            Serial.print("   Angle: ");
            Serial.print(angle, 2);
            Serial.print(" deg   Total: ");
            Serial.println(totalDeg, 2);
        } else if (input == "f") {
            doForward();
            doStop();
        }

        // ---- Unknown command ----
        else {
            Serial.print("Unknown command: ");
            Serial.println(input);
        }
    }
}

