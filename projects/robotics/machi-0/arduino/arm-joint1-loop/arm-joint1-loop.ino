/*

AS5600 to MKR WiFi 1010 (I2C Communication):
AS5600 VCC → MKR *5V
AS5600 GND → MKR GND
AS5600 SCL → MKR SCL (Pin A21)
AS5600 SDA → MKR SDA (Pin A22)


L298N Pin	Connect To (MKR WiFi 1010)	Description
ENA	                  D4	PWM speed / enable
IN1	                  D2	Motor direction 1
IN2	                  D3	Motor direction 2
12V	External power (motor supply, e.g. 9–12 V)	Power for motor
GND	Common ground with MKR	Ground reference
OUT1, OUT2	Motor terminals	Motor output
5V (from L298 board)	Do NOT connect to MKR 5 V	(L298 onboard regulator may not match MKR’s 3.3 V logic)

*/

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
const int TOLERANCE = 20;   // degrees tolerance
const int MAX_PWM = 255;   // MKR analogWrite range (0-255)
const int MIN_PWM = 200;    // minimum PWM to overcome stiction
const int DES_PWM = 100;    // minimum PWM to overcome stiction

// --- smoothing / ramping ---
const int MAX_PWM_STEP = 200;   // max change in PWM per loop (tune smaller for smoother)
static int lastPwm = 0;        // last applied PWM magnitude
static int lastDir = 0;        // last applied direction (-1,0,1)

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
  Wire.beginTransmission((uint8_t)AS5600_ADDR); // Explicitly cast AS5600_ADDR to uint8_t
  Wire.write(0x0E);  // ANGLE register high byte
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)AS5600_ADDR, (uint8_t)2); // Explicitly cast both arguments to uint8_t
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

// Modify the code to accept time in milliseconds as input and calculate revolutions and residual angle

void loop() {
  // read time input from serial (line-based). Example: "5000" for 5000 ms
  if (Serial.available() > 0) {
    String s = Serial.readStringUntil('\n');
    s.trim();
    if (s.length() > 0) {
      long inputTime = s.toInt(); // parse time in milliseconds
      if (inputTime > 0) {
        Serial.print("Running motor for ");
        Serial.print(inputTime);
        Serial.println(" ms...");

        // Initialize counters
        float initialAngle = readAngleDeg();
        if (isnan(initialAngle)) {
          Serial.println("AS5600 read error");
          return;
        }
        float lastAngle = initialAngle;
        int revolutions = 0;
        unsigned long startTime = millis();

        // Run motor for the specified time
        while (millis() - startTime < inputTime) {
          float currentAngle = readAngleDeg();
          if (isnan(currentAngle)) {
            Serial.println("AS5600 read error");
            break;
          }

          // Calculate angle difference
          float delta = currentAngle - lastAngle;
          if (delta > 180.0) delta -= 360.0;
          else if (delta < -180.0) delta += 360.0;

          // Update revolutions
          if (delta > 0) revolutions += (int)(delta / 360.0);
          else revolutions -= (int)(-delta / 360.0);

          lastAngle = currentAngle;
          delay(20); // Small delay to avoid excessive polling
        }

        // Calculate residual angle
        float finalAngle = readAngleDeg();
        if (isnan(finalAngle)) {
          Serial.println("AS5600 read error");
          return;
        }
        float residualAngle = fmod(finalAngle, 360.0);
        if (residualAngle < 0) residualAngle += 360.0;

        // Output results
        Serial.print("Revolutions: ");
        Serial.println(revolutions);
        Serial.print("Residual Angle: ");
        Serial.print(residualAngle, 2);
        Serial.println("°");
      } else {
        Serial.println("Invalid time input. Please enter a positive number.");
      }
    }
  }

  delay(50); // Loop delay
}
