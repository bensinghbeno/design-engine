#include <Wire.h>
#include <mcp_can.h>
#include <SPI.h>

#define AS5600_ADDR 0x36   // I2C address for AS5600

const int SPI_CS_PIN = 7;
const int CAN_INT_PIN = 6; // INT pin for MCP2515 (active low)
MCP_CAN CAN(SPI_CS_PIN);

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
  SPI.begin();
  pinMode(CAN_INT_PIN, INPUT_PULLUP);

  // initialize CAN (MCP2515)
  if (CAN.begin(MCP_ANY, CAN_500KBPS, MCP_8MHZ) == CAN_OK)
    Serial.println("CAN init OK!");
  else
    Serial.println("CAN init FAIL!");
  CAN.setMode(MCP_NORMAL);

  delay(100);
  Serial.println("AS5600 + L298 closed-loop (with unwrap)");
  Serial.println("Send target angle (e.g. 180.3) followed by Enter (or send CAN id 0x100 with 16-bit angle)");
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
//
// Updated: allow starting from a position that lies in a blocked interval
// and immediately move into the allowed region (e.g. from 352° -> 310°).
// We only permit this special-case: start is inside a blocked interval and
// the movement direction goes out of that blocked interval into the allowed
// range (i.e. the only blocked intersection touches the start point).
bool pathCrossesBlocked(float a, float b, bool allowStartInBlocked = false) {
  float origStart = a;
  float origEnd = b;

  float start = a;
  float end = b;
  if (start > end) {
    float t = start; start = end; end = t;
  }

  // choose m range that covers start..end
  int m_start = (int)floor(start / 360.0f) - 1;
  int m_end   = (int)ceil(end / 360.0f) + 1;
  const float EPS = 1e-4f;

  for (int m = m_start; m <= m_end; ++m) {
    // blocked interval 1: [360*m, ALLOWED_MIN + 360*m)
    float b1s = 360.0f * m;
    float b1e = ALLOWED_MIN + 360.0f * m;
    float is = max(start, b1s);
    float ie = min(end, b1e);
    if (ie > is + EPS) {
      // intersection exists
      bool origStartInThisBlocked = (origStart >= b1s - EPS && origStart < b1e - EPS);
      if (origStartInThisBlocked && allowStartInBlocked) {
        // allow only if movement goes OUT of this blocked interval immediately,
        // i.e. origStart lies at the intersection boundary that is adjacent to the allowed region
        // and the movement direction is towards the allowed region.
        // Determine movement direction on number line:
        if (origStart > origEnd) {
          // moving decreasing: intersection end should equal origStart
          if (fabs(origStart - ie) < EPS) {
            // ignore this intersection
          } else {
            return true;
          }
        } else {
          // moving increasing: intersection start should equal origStart
          if (fabs(origStart - is) < EPS) {
            // ignore this intersection
          } else {
            return true;
          }
        }
      } else {
        return true;
      }
    }

    // blocked interval 2: [ALLOWED_MAX + 360*m, 360*(m+1))
    float b2s = ALLOWED_MAX + 360.0f * m;
    float b2e = 360.0f * (m + 1);
    is = max(start, b2s);
    ie = min(end, b2e);
    if (ie > is + EPS) {
      bool origStartInThisBlocked = (origStart >= b2s - EPS && origStart < b2e - EPS);
      if (origStartInThisBlocked && allowStartInBlocked) {
        if (origStart > origEnd) {
          // moving decreasing: intersection end should equal origStart
          if (fabs(origStart - ie) < EPS) {
            // ignore this intersection
          } else {
            return true;
          }
        } else {
          // moving increasing: intersection start should equal origStart
          if (fabs(origStart - is) < EPS) {
            // ignore this intersection
          } else {
            return true;
          }
        }
      } else {
        return true;
      }
    }
  }
  return false;
}

// Send status back on CAN ID 0x101:
// bytes 0..1 : raw angle in tenths (int16 BE)
// bytes 2..3 : continuous angle in tenths (int16 BE)
// byte  4    : on-target flag (0/1)
void sendStatusFrame(float rawDeg, float continuousDeg, bool onTarget) {
  int16_t rawTenths = (int16_t)round(rawDeg * 10.0f);
  int16_t contTenths = (int16_t)round(continuousDeg * 10.0f);
  uint8_t data[5];
  data[0] = (rawTenths >> 8) & 0xFF;
  data[1] = rawTenths & 0xFF;
  data[2] = (contTenths >> 8) & 0xFF;
  data[3] = contTenths & 0xFF;
  data[4] = onTarget ? 1 : 0;
  CAN.sendMsgBuf(0x101, 0, 5, data);
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

  // --- CAN input handling ---
  // Expect CAN frame ID 0x100 with first two bytes = big-endian 16-bit angle in tenths of degree
  // (e.g. 1803 -> 180.3°). Adjust decoding if your sender uses a different encoding.
  if (!digitalRead(CAN_INT_PIN)) { // INT goes low when a message arrives
    long unsigned int rxId;
    unsigned char len = 0;
    unsigned char rxBuf[8];
    CAN.readMsgBuf(&rxId, &len, rxBuf);
    if (rxId == 0x100 && len >= 2) {
      uint16_t rawVal = ((uint16_t)rxBuf[0] << 8) | rxBuf[1];
      float a = rawVal / 10.0f; // convert tenths -> degrees
      // normalize 0..360
      while (a < 0) a += 360.0;
      while (a >= 360.0) a -= 360.0;

      if (a < ALLOWED_MIN || a > ALLOWED_MAX) {
        haveTarget = false;
        Serial.print("CAN Rejected: ");
        Serial.print(a, 2);
        Serial.println("° outside allowed range.");
      } else {
        targetAngle = a;
        haveTarget = true;
        Serial.print("CAN Target set: ");
        Serial.println(targetAngle, 2);
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

  // send periodic status (receiver -> sender)
  // set onTarget below and send appropriate flag in both branches
  if (!haveTarget) {
    stopMotor();
    // report not-on-target
    sendStatusFrame(raw, continuousAngle, false);
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
    if (!pathCrossesBlocked(continuousAngle, cand, true)) {
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
    haveTarget = false;
    stopMotor();
    Serial.println("No safe path to target without entering blocked range — command cancelled.");
    // report cancelled / not-on-target
    sendStatusFrame(raw, continuousAngle, false);
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
    // report on-target
    sendStatusFrame(raw, continuousAngle, true);
  } else {
    int pwm = (int)(Kp * absErr);
    pwm = constrain(pwm, MIN_PWM, MAX_PWM);
    int dir = (err > 0) ? 1 : -1;
    driveMotor(dir, pwm);
    Serial.print("CurC: ");
    Serial.print(continuousAngle, 2);
    Serial.print("°  TgtC: ");
    Serial.print(targetContinuous, 2);
    Serial.print("°  Err: ");
    Serial.print(err, 2);
    Serial.print("°  PWM: ");
    Serial.println(pwm);
    // report moving / not-on-target
    sendStatusFrame(raw, continuousAngle, false);
  }

  delay(20); // loop rate — adjust as needed
}
