#include <Wire.h>

#define AS5600_ADDR 0x36
#define ANGLE_HIGH  0x0E
#define ANGLE_LOW   0x0F

// Motor pins
#define L298_ENA 4
#define L298_IN1 2
#define L298_IN2 3

// PWM speed levels
#define PWM_LOW 100
#define PWM_HIGH 100

volatile long revCount = 0;
uint16_t lastRaw = 0;

uint16_t readRawAngle() {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(ANGLE_HIGH);
  Wire.endTransmission(false);

  Wire.requestFrom(AS5600_ADDR, 2);
  uint8_t high = Wire.read();
  uint8_t low  = Wire.read();

  return ((high & 0x0F) << 8) | low;   // 0–4095
}

void setup() {
  Serial.begin(115200);

  Wire.begin();
  Wire.setClock(400000); // Fast I2C

  pinMode(L298_ENA, OUTPUT);
  pinMode(L298_IN1, OUTPUT);
  pinMode(L298_IN2, OUTPUT);

  delay(200);

  lastRaw = readRawAngle();

  Serial.println("AS5600 TRUE Angle + Multi-Turn READY");
  Serial.println("Send target TOTAL degrees (ex: 3610 = 1 rev + 10 deg)");
}

void motorCW(int pwm) {
  digitalWrite(L298_IN1, HIGH);
  digitalWrite(L298_IN2, LOW);
  analogWrite(L298_ENA, pwm);
}

void motorCCW(int pwm) {
  digitalWrite(L298_IN1, LOW);
  digitalWrite(L298_IN2, HIGH);
  analogWrite(L298_ENA, pwm);
}

void motorStop() {
  analogWrite(L298_ENA, 0);
  digitalWrite(L298_IN1, LOW);
  digitalWrite(L298_IN2, LOW);
}

float readAngleDeg() {
  uint16_t raw = readRawAngle();
  int diff = raw - lastRaw;

  // multi-turn rollover detection
  if (diff > 2048)  revCount--;
  else if (diff < -2048) revCount++;

  lastRaw = raw;

  float angleDeg = raw * 360.0 / 4096.0;     // physical angle
  float totalDeg = (revCount * 360.0) + angleDeg;  // multi-turn absolute
  return totalDeg;
}

// Return total encoder counts (multi-turn) using the same rollover logic
long readTotalCounts() {
  uint16_t raw = readRawAngle();
  int diff = raw - lastRaw;

  if (diff > 2048) revCount--;
  else if (diff < -2048) revCount++;

  lastRaw = raw;

  // total counts = revCount * 4096 + raw
  long total = (revCount * 4096L) + (long)raw;
  return total;
}

void loop() {

  static float targetDeg = 0;
  static bool hasTarget = false;

  // --- Handle serial input target ---
  if (Serial.available()) {
    targetDeg = Serial.parseFloat();
    hasTarget = true;
    Serial.print("Target total degrees = ");
    Serial.println(targetDeg);
    delay(1000);
  }

  // Read current position in counts and degrees (single read to keep revCount consistent)
  long currCounts = readTotalCounts();
  float currDeg = currCounts * 360.0 / 4096.0;

  // Always print current (true) angle
  Serial.print("Angle = ");
  Serial.print(currDeg, 2);
  Serial.println(" deg");

  if (hasTarget) {
    // Convert target (degrees) to counts for robust multi-turn comparison
    long targetCounts = lround(targetDeg * 4096.0 / 360.0);
    long diffCounts = targetCounts - currCounts;
    long absDiff = labs(diffCounts);

    const long bufferCounts = 1000; // user requested buffer angle (in counts)
    const long pwmThreshold = 5000; // user requested threshold (in counts)

    if (absDiff <= bufferCounts) {
      motorStop();
      Serial.println("Reached (within buffer).\n");
      hasTarget = false; // Done
    } else {
      int pwm = (absDiff < pwmThreshold) ? PWM_LOW : PWM_HIGH;
      if (diffCounts > 0) motorCW(pwm);
      else                motorCCW(pwm);

      Serial.print("Target counts = "); Serial.println(targetCounts);
      Serial.print("Diff counts = "); Serial.println(diffCounts);
      Serial.print("PWM = "); Serial.println(pwm);
    }
  } else {
    motorStop();
  }

  delay(1000);   // update rate ~50 Hz
}
