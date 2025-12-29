// Open loop motor control example - SAFE MODE VERSION
#include <SimpleFOC.h>

#include <Wire.h>
// --- Custom AS5600 Sensor Code Integration ---
const uint8_t AS5600_ADDR = 0x36; // I2C address for AS5600
#define COUNTS_PER_REV 4096       // 12-bit resolution
bool initialized = false;
uint16_t prevRaw = 0;
int32_t totalTicks = 0; // signed cumulative tick count since zero


// Function to read the raw angle from AS5600
uint16_t readAngleRaw()
{
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(0x0E); // Start address for angle high byte
  if (Wire.endTransmission() != 0)
    return 0xFFFF; // comms error

  Wire.requestFrom((uint8_t)AS5600_ADDR, (uint8_t)2); // unambiguous overload
  if (Wire.available() == 2)
  {
    uint8_t highByte = Wire.read();
    uint8_t lowByte = Wire.read();
    return ((highByte & 0x0F) << 8) | lowByte; // 12-bit angle
  }
  return 0xFFFF; // error
}

// BLDC motor & driver instance
BLDCMotor motor = BLDCMotor(11);
BLDCDriver3PWM driver = BLDCDriver3PWM(9, 5, 6, 8);

// target variable
float target_velocity = 0;

// Commander
Commander command = Commander(Serial);

// === COMMAND HANDLERS ===

void doRPM(char *cmd)
{
  float rpm_target;
  command.scalar(&rpm_target, cmd);
  target_velocity = rpm_target * _RPM_TO_RADS;

  // Enable motor and driver
  driver.enable();
  motor.enable();

  // Move motor at target velocity
  motor.move(target_velocity);

  Serial.print("Motor running at RPM: ");
  Serial.println(rpm_target);
}

void doLimit(char *cmd)
{
  command.scalar(&motor.voltage_limit, cmd);
}

// Disable motor + driver (full safe idle)
void doDisable(char *cmd)
{
  motor.disable();
  driver.disable();
  Serial.println("== SAFE MODE: Motor & Driver DISABLED ==");
}

// Enable motor + driver (begin open-loop control)
void doEnable(char *cmd)
{
  driver.enable();
  motor.enable();
  Serial.println("== CONTROL MODE ENABLED ==");
}

void setup()
{

  Serial.begin(115200);
  delay(500);

  // Wait until AS5600 is detected
  Wire.begin(); // Join I2C bus (UNO: SDA=A4, SCL=A5)
  delay(500);
  Serial.print("Scanning for AS5600 at address 0x");
  Serial.print(AS5600_ADDR, HEX);
  Serial.println("...");

  while (true)
  {
    Wire.beginTransmission(AS5600_ADDR);
    if (Wire.endTransmission() == 0)
    {
      Serial.println("AS5600 found!");
      break; // Exit the loop once the sensor is detected
    }
    delay(1000); // Wait a second before retrying
  }

  SimpleFOCDebug::enable(&Serial);

  // --- DRIVER SETUP ---
  driver.voltage_power_supply = 12;
  driver.voltage_limit = 6;

  if (!driver.init())
  {
    Serial.println("Driver init failed!");
    return;
  }

  // --- MOTOR SETUP ---
  motor.linkDriver(&driver);
  motor.voltage_limit = 6;
  motor.controller = MotionControlType::velocity_openloop;

  if (!motor.init())
  {
    Serial.println("Motor init failed!");
    return;
  }

  // --- SAFE MODE ENGAGED IMMEDIATELY AFTER RESET ---
  motor.disable();
  driver.disable();
  Serial.println("==============================");
  Serial.println("   SYSTEM STARTED IN SAFE MODE");
  Serial.println("   No torque. Motor is COASTING.");
  Serial.println("   Send 'E' to ENABLE control.");
  Serial.println("==============================");

  doDisplayAngle();

  // Commander commands
  command.add('R', doRPM, "target RPM");
  command.add('L', doLimit, "voltage limit");
  command.add('X', doDisable, "disable outputs (safe mode)");
  command.add('E', doEnable, "enable motor/driver");
  command.add('C', doClockwiseRPM, "run clockwise at RPM for 5 sec");
  command.add('D', doDisplayAngle, "display Angle");
  command.add('A', doAntiClockwiseRPM, "run counterclockwise at RPM for 5 sec");
}

// Helper function to replace delay() since Timer0 is used by PWM on pins 5 & 6
void delay_safe(unsigned long ms)
{
  for (unsigned long i = 0; i < ms; i++)
  {
    delayMicroseconds(1000);
  }
}

void doDisplayAngle()
{
  doDisable('X');

  uint16_t raw = readAngleRaw();
  if (raw == 0xFFFF)
  {
    Serial.println("Read error");
    return;
  }

  // Display the raw angle in degrees
  float rawAngleDegrees = (raw * 360.0f) / COUNTS_PER_REV;
  Serial.print("Current angle in degrees :: ");
  Serial.println(rawAngleDegrees, 2);
}

// Command handler for running motor clockwise at a specific RPM for 5 seconds
void doClockwiseRPM(char* cmd) {
  float rpm_target;
  command.scalar(&rpm_target, cmd); 
  target_velocity = rpm_target * _RPM_TO_RADS;

  // Enable motor and driver
  driver.enable();
  motor.enable();

  // Move motor at target velocity for 5 seconds
  unsigned long start_time = millis();
  while (millis() - start_time < 5000) {
    motor.move(target_velocity);
  }

  // Stop the motor after 5 seconds
  target_velocity = 0;
  motor.move(target_velocity);

  // Disable motor and driver
  motor.disable();
  driver.disable();

  Serial.print("Motor ran clockwise at RPM: ");
  Serial.print(rpm_target);
  Serial.println(" for 5 seconds.");
  doDisplayAngle();
}

// Command handler for running motor counterclockwise at a specific RPM for 5 seconds
void doAntiClockwiseRPM(char* cmd) {
  float rpm_target;
  command.scalar(&rpm_target, cmd); 
  target_velocity = -rpm_target * _RPM_TO_RADS; // Negative for counterclockwise

  // Enable motor and driver
  driver.enable();
  motor.enable();

  // Move motor at target velocity for 5 seconds
  unsigned long start_time = millis();
  while (millis() - start_time < 5000) {
    motor.move(target_velocity);
  }

  // Stop the motor after 5 seconds
  target_velocity = 0;
  motor.move(target_velocity);

  // Disable motor and driver
  motor.disable();
  driver.disable();

  Serial.print("Motor ran counterclockwise at RPM: ");
  Serial.print(rpm_target);
  Serial.println(" for 5 seconds.");
  doDisplayAngle();
}

void loop()
{
  motor.move(target_velocity);
  command.run();

}

