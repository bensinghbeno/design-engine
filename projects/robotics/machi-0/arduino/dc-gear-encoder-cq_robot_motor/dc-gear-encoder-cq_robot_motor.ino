// ----- MOTOR PINS -----
#define ENA 9
#define IN1 8
#define IN2 7

// ----- ENCODER PINS -----
#define ENC_A 2
#define ENC_B 3

// ----- MOTOR SETTINGS -----
const int PWM_SPEED = 150;      // normal PWM speed
const int PWM_APPROACH = 60;    // slower speed near target
const int CPR = 64;             // encoder counts per motor shaft rev
const int GEAR_RATIO = 270;     // gearbox ratio
const float COUNTS_PER_REV = CPR * GEAR_RATIO * 4.0; // quadrature x4
const float TOLERANCE_DEG = 10.0; // buffer to stop motor safely

// ----- VARIABLES -----
volatile long encoderCount = 0;
long targetCount = 0;
bool movingToTarget = false;

// remember angles (degrees). startup = 0
float currentAngleDeg = 0.0;
float targetAngleDeg = 0.0;

// track last reported encoder count so we can print a relative delta each time
volatile long lastReportedCount = 0;

// ----- SETUP -----
void setup() {
  Serial.begin(9600);

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENC_A, INPUT_PULLUP);
  pinMode(ENC_B, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(ENC_A), encoderAChange, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_B), encoderBChange, CHANGE);

  Serial.println("Motor + Encoder Ready");
  Serial.println("Commands:");
  Serial.println("  f = forward");
  Serial.println("  r = reverse");
  Serial.println("  s = stop");
  Serial.println("  <counts> = rotate by encoder counts (relative, +/-)");
}

// ----- LOOP -----
void loop() {
  // keep currentAngleDeg in sync with encoder (read atomically)
  noInterrupts();
  long enc = encoderCount;
  interrupts();
  currentAngleDeg = ((float)enc / COUNTS_PER_REV) * 360.0;

  // ----- SERIAL INPUT -----
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "f") {
      movingToTarget = false;
      driveMotor(true, PWM_SPEED);
      delay(2000);
      stopMotor();
      printRevs();
    } 
    else if (cmd == "r") {
      movingToTarget = false;
      driveMotor(false, PWM_SPEED);
      delay(2000);
      stopMotor();
      printRevs();
    } 
    else if (cmd == "s") {
      stopMotor();
      movingToTarget = false;
      Serial.println("Stopped");
      printRevs(); // show relative encoder delta for this command
    } 
    else {
      // assume numeric encoder-count delta (relative)
      long deltaCounts = cmd.toInt();            // relative encoder counts (+/-)
      // set absolute target as current encoder count + delta
      noInterrupts();
      long curEnc = encoderCount;
      interrupts();
      targetCount = curEnc + deltaCounts;
      // also compute the equivalent absolute angle for info
      targetAngleDeg = ((float)targetCount / COUNTS_PER_REV) * 360.0;
      movingToTarget = true;
      Serial.print("Target set: delta counts = ");
      Serial.print(deltaCounts);
      Serial.print("  targetCount = ");
      Serial.print(targetCount);
      Serial.print("  (angle ");
      Serial.print(targetAngleDeg, 2);
      Serial.println(" deg)");
      printRevs(); // show encoder count at command time
    }
  }

  // ----- TARGET CONTROL -----
  if (movingToTarget) {
    long error = targetCount - encoderCount;
    float errorDeg = ((float)error / COUNTS_PER_REV) * 360.0;

    if (fabs(errorDeg) <= TOLERANCE_DEG) {
      stopMotor();
      movingToTarget = false;
      currentAngleDeg = targetAngleDeg;
      printRevs();
      Serial.println("Target reached within buffer");
    } else {
      int pwm = (fabs(errorDeg) < 50.0) ? PWM_APPROACH : PWM_SPEED;
      driveMotor(error > 0, pwm);
    }
  }

  delay(5);
}

// ----- MOTOR FUNCTIONS -----
void driveMotor(bool forward, int pwm) {
  // POLARITY REVERSED
  digitalWrite(IN1, forward ? LOW : HIGH);
  digitalWrite(IN2, forward ? HIGH : LOW);
  analogWrite(ENA, pwm);
}

void stopMotor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 0);
}

// ----- ENCODER ISRs -----
void encoderAChange() {
  int a = digitalRead(ENC_A);
  int b = digitalRead(ENC_B);
  encoderCount += (a == b) ? 1 : -1; // sign reversed
}

void encoderBChange() {
  int a = digitalRead(ENC_A);
  int b = digitalRead(ENC_B);
  encoderCount += (a != b) ? 1 : -1; // sign reversed
}

// ----- HELPER FUNCTIONS -----
void printRevs() {
  // read encoder atomically
  noInterrupts();
  long enc = encoderCount;
  interrupts();

  // relative delta since last time printRevs() was called
  long delta = enc - lastReportedCount;

  Serial.print("Encoder count: ");
  Serial.print(enc);
  Serial.print("  (delta: ");
  Serial.print(delta);
  Serial.println(")");

  // update last reported count so next call shows relative movement only
  lastReportedCount = enc;

  float totalDeg = ((float)enc / COUNTS_PER_REV) * 360.0;
  int fullRevs = (int)floor(totalDeg / 360.0);
  float deg = totalDeg - (fullRevs * 360.0);

  if (deg > 180.0) deg -= 360.0;
  if (deg < -180.0) deg += 360.0;

  Serial.print("Rotation: ");
  Serial.print(fullRevs);
  Serial.print(" rev(s) + ");
  Serial.print(deg, 2);
  Serial.println(" deg");
}

void resetEncoder() {
  noInterrupts();
  encoderCount = 0;
  interrupts();
}
