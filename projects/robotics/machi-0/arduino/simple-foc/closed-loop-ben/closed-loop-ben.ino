#include <SimpleFOC.h>
#include <Wire.h>

// --- AS5600 Sensor Configuration ---
const uint8_t AS5600_ADDR = 0x36;
#define COUNTS_PER_REV 4096

// --- Motor & Driver Configuration ---
// Using 11 Pole Pairs to match your working open-loop reference
BLDCMotor motor = BLDCMotor(11);
BLDCDriver3PWM driver = BLDCDriver3PWM(9, 5, 6, 8);

// --- Control Variables ---
float target_angle = 0.0;      // Target angle in degrees
float current_angle = 0.0;     // Current angle in degrees
float target_velocity = 0.0;   // Velocity command sent to motor

// Settings
const float MOVE_RPM = 20.0;    // Speed to move towards target
const float TOLERANCE = 0.2;   // Stop if within +/- 2 degrees
const float FORBIDDEN_MIN = 30.0;
const float FORBIDDEN_MAX = 90.0;

// Commander interface
Commander command = Commander(Serial);

// --- Helper: Safe Delay (Fixes Timer0 conflict on UNO pins 5&6) ---
void delay_safe(unsigned long ms)
{
  for (unsigned long i = 0; i < ms; i++)
  {
    delayMicroseconds(1000);
  }
}

// --- Helper: Read Raw Angle from AS5600 (From Reference) ---
uint16_t readAngleRaw()
{
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(0x0E); // Start address for angle high byte
  if (Wire.endTransmission() != 0)
    return 0xFFFF; // comms error

  Wire.requestFrom((uint8_t)AS5600_ADDR, (uint8_t)2);
  if (Wire.available() == 2)
  {
    uint8_t highByte = Wire.read();
    uint8_t lowByte = Wire.read();
    return ((highByte & 0x0F) << 8) | lowByte; // 12-bit angle
  }
  return 0xFFFF; // error
}

// --- Helper: Get Angle in Degrees ---
float getAngleDegrees() {
  uint16_t raw = readAngleRaw();
  if (raw == 0xFFFF) return -1.0; // Return -1 on error
  return (raw * 360.0f) / COUNTS_PER_REV;
}

// --- Command: Set Target Angle ---
void doTarget(char* cmd) {
  float new_target;
  command.scalar(&new_target, cmd);
  
  // Normalize to 0-360
  while (new_target >= 360.0) new_target -= 360.0;
  while (new_target < 0.0) new_target += 360.0;

  if (new_target > FORBIDDEN_MIN && new_target < FORBIDDEN_MAX) {
    Serial.println("REJECTED: Target in forbidden zone (30-90)!");
    return;
  }

  target_angle = new_target;
  Serial.print("Target set to: ");
  Serial.println(target_angle);
}

// --- Command: Display Angle (From Reference Logic) ---
void doDisplayAngle(char* cmd) {
  float angle = getAngleDegrees();
  Serial.print("Current angle in degrees :: ");
  Serial.println(angle, 2);
}

void setup() {
  Serial.begin(115200);
  
  // 1. Initialize I2C
  Wire.begin();
  delay_safe(500);
  Serial.print("Scanning for AS5600 at address 0x");
  Serial.print(AS5600_ADDR, HEX);
  Serial.println("...");

  while (true)
  {
    Wire.beginTransmission(AS5600_ADDR);
    if (Wire.endTransmission() == 0)
    {
      Serial.println("AS5600 found!");
      break;
    }
    delay_safe(1000);
  }

  // 2. Initialize Driver
  driver.voltage_power_supply = 12;
  driver.voltage_limit = 6;
  if (!driver.init()) {
    Serial.println("Driver init failed!");
    while(1);
  }

  // 3. Initialize Motor (Open Loop Velocity Mode)
  motor.linkDriver(&driver);
  motor.voltage_limit = 6;
  motor.controller = MotionControlType::velocity_openloop;
  if (!motor.init()) {
    Serial.println("Motor init failed!");
    while(1);
  }

  // 4. Set Initial Target to Current Position (Prevent jump at start)
  float start_angle = getAngleDegrees();
  if (start_angle >= 0) {
    target_angle = start_angle;
  }

  // 5. Setup Serial Commands
  command.add('T', doTarget, "Set Target Angle (deg)");
  command.add('D', doDisplayAngle, "Display Current Angle");

  Serial.println("Custom Closed Loop Ready.");
  Serial.println("Send 'T 90' to move to 90 degrees.");
  doDisplayAngle('D');
}

void loop() {
  // 1. Read Sensor
  float angle = getAngleDegrees();
  
  // If sensor read failed, stop motor and skip logic
  if (angle < 0) {
    motor.move(0);
    command.run();
    return;
  }
  current_angle = angle;

  // 2. Calculate Error (Avoid Forbidden Zone Logic)
  // Map angles [0, 30] to [360, 390] so the safe range is contiguous [90, 390]
  float current_mapped = (current_angle <= FORBIDDEN_MIN) ? current_angle + 360.0 : current_angle;
  float target_mapped = (target_angle <= FORBIDDEN_MIN) ? target_angle + 360.0 : target_angle;

  float error = target_mapped - current_mapped;

  // 3. Control Logic (Bang-Bang with Deadband)
  if (abs(error) > TOLERANCE) {
    if (error > 0) {
      target_velocity = MOVE_RPM * _RPM_TO_RADS; // Clockwise
    } else {
      target_velocity = -MOVE_RPM * _RPM_TO_RADS; // Counter-Clockwise
    }
  } else {
    target_velocity = 0; // Stop at target
  }

  // 4. Move Motor & Check Commands
  motor.move(target_velocity);
  command.run();
}
