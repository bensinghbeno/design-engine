#include <Wire.h>

#define AS5600_ADDR 0x36   // I2C address for AS5600

const int IN1 = 2;
const int IN2 = 3;
const int ENA = 4;  // PWM pin (speed / enable)

const float Kp = 1.6;      // proportional gain — tune on your setup
const int TOLERANCE = 5;   // degrees tolerance
const int MAX_PWM = 255;   // MKR analogWrite range (0-255)
const int MIN_PWM = 150;    // minimum PWM to overcome stiction

// allowed range (only inputs inside this range are accepted)
const float ALLOWED_MIN = 100.0;
const float ALLOWED_MAX = 330.0;

float targetAngle = 0.0;
bool haveTarget = false;

// for unwrap / continuous angle tracking
float lastRawAngle = NAN;
float continuousAngle = 0.0;
bool haveAngleInit = false;

void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);

  // Ensure motor stopped
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 0); // motor disabled / 0 speed

  Serial.begin(9600);
  Wire.begin();
  delay(100);
  Serial.println("AS5600 + L298 closed-loop (with unwrap)");
  Serial.println("Send target angle (e.g. 180.3) followed by Enter");
}

uint16_t readAngleRaw() {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(0x0E);  // ANGLE register high byte
  Wire.endTransmission(false);
  Wire.requestFrom(AS5600_ADDR, (uint8_t)2);
  if (Wire.available() == 2) {
    uint8_t high = Wire.read();
    uint8_t low  = Wire.read();
    return ((high & 0x0F) << 8) | low; // 12-bit value
  }
  return 0xFFFF;
}

float readAngleDeg() {
  uint16_t raw = readAngleRaw();
  if (raw == 0xFFFF) return NAN;
  return (raw * 360.0) / 4096.0;
}

void stopMotor() {
  analogWrite(ENA, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}

void driveMotor(int dir, int pwm) {
  pwm = constrain(pwm, 0, MAX_PWM);
  if (dir > 0) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  } else if (dir < 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
  }
  analogWrite(ENA, pwm);
}

// returns true if the straight path on the continuous number line from a->b
// intersects any BLOCKED interval (outside ALLOWED_MIN..ALLOWED_MAX)
// blocked intervals per revolution: [360*m, ALLOWED_MIN + 360*m) and
// [ALLOWED_MAX + 360*m, 360*(m+1))
bool pathCrossesBlocked(float a, float b) {
  float start = a;
  float end = b;
  if (start > end) {
    float t = start; start = end; end = t;
  }
  // choose m range that covers start..end
  int m_start = (int)floor(start / 360.0f) - 1;
  int m_end   = (int)ceil(end / 360.0f) + 1;
  for (int m = m_start; m <= m_end; ++m) {
    // blocked interval 1: [360*m, ALLOWED_MIN + 360*m)
    float b1s = 360.0f * m;
    float b1e = ALLOWED_MIN + 360.0f * m;
    if (!(end <= b1s || start >= b1e)) return true;
    // blocked interval 2: [ALLOWED_MAX + 360*m, 360*(m+1))
    float b2s = ALLOWED_MAX + 360.0f * m;
    float b2e = 360.0f * (m + 1);
    if (!(end <= b2s || start >= b2e)) return true;
  }
  return false;
}

void loop() {
  // read angle command from serial (line-based). Example: "180.3"
  if (Serial.available() > 0) {
    String s = Serial.readStringUntil('\n');
    s.trim();
    if (s.length() > 0) {
      float a = s.toFloat(); // parses floats like 180.3
      if (!isnan(a)) {
        // normalize 0..360
        while (a < 0) a += 360.0;
        while (a >= 360.0) a -= 360.0;

        // accept only inputs inside allowed range
        if (a < ALLOWED_MIN || a > ALLOWED_MAX) {
          haveTarget = false;
          Serial.print("Rejected: input ");
          Serial.print(a, 2);
          Serial.print("° is outside allowed range [");
          Serial.print(ALLOWED_MIN, 1);
          Serial.print("°, ");
          Serial.print(ALLOWED_MAX, 1);
          Serial.println("°]. Allowed: [150,350].");
        } else {
          targetAngle = a;
          haveTarget = true;
          Serial.print("Target set: ");
          Serial.println(targetAngle, 2);
        }
      } else {
        Serial.println("Invalid angle input");
      }
    }
  }

  float raw = readAngleDeg();
  if (isnan(raw)) {
    Serial.println("AS5600 read error");
    delay(150);
    return;
  }

  // UNWRAP / continuous angle tracking:
  if (!haveAngleInit) {
    continuousAngle = raw;
    lastRawAngle = raw;
    haveAngleInit = true;
  } else {
    float delta = raw - lastRawAngle;
    // map delta into (-180..180]
    if (delta > 180.0) delta -= 360.0;
    else if (delta <= -180.0) delta += 360.0;
    continuousAngle += delta;
    lastRawAngle = raw;
  }

  Serial.print("Raw: ");
  Serial.print(raw, 2);
  Serial.print("°  Continuous: ");
  Serial.print(continuousAngle, 2);
  Serial.println("°");

  if (!haveTarget) {
    stopMotor();
    delay(50);
    return;
  }

  // find a targetContinuous that does NOT require passing through blocked intervals
  // search several wraps of the requested target (n = -3..3)
  bool foundSafe = false;
  float bestCandidate = NAN;
  float bestErr = 1e9;
  for (int n = -3; n <= 3; ++n) {
    float cand = targetAngle + 360.0f * n;
    // check path from continuousAngle to cand does NOT cross blocked intervals
    if (!pathCrossesBlocked(continuousAngle, cand)) {
      float e = fabs(cand - continuousAngle);
      if (e < bestErr) {
        bestErr = e;
        bestCandidate = cand;
        foundSafe = true;
      }
    }
  }

  float targetContinuous;
  if (foundSafe) {
    targetContinuous = bestCandidate;
  } else {
    // no safe continuous target found within checked wraps => reject and stop motor
    haveTarget = false;
    stopMotor();
    Serial.println("No safe path to target without entering blocked range — command cancelled.");
    delay(200);
    return;
  }

  float err = targetContinuous - continuousAngle; // signed error (deg)
  float absErr = fabs(err);

  if (absErr <= TOLERANCE) {
    stopMotor();
    Serial.print("On target: ");
    Serial.print(continuousAngle, 2);
    Serial.print("°  (target ");
    Serial.print(targetContinuous, 2);
    Serial.println("°)");
  } else {
    int pwm = (int)(Kp * absErr);
    pwm = constrain(pwm, MIN_PWM, MAX_PWM);
    int dir = (err > 0) ? 1 : -1; // positive error -> increase continuous angle
    driveMotor(dir, pwm);
    Serial.print("CurC: ");
    Serial.print(continuousAngle, 2);
    Serial.print("°  TgtC: ");
    Serial.print(targetContinuous, 2);
    Serial.print("°  Err: ");
    Serial.print(err, 2);
    Serial.print("°  PWM: ");
    Serial.println(pwm);
  }

  delay(20); // loop rate — adjust as needed
}
