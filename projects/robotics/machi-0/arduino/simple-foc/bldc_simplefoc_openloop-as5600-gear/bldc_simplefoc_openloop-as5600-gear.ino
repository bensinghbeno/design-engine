// Open loop motor control example - SAFE MODE VERSION
#include <SimpleFOC.h>

#include <Wire.h>
// --- Custom AS5600 Sensor Code Integration ---
const uint8_t AS5600_ADDR = 0x36;   // I2C address for AS5600
#define COUNTS_PER_REV 4096  // 12-bit resolution
bool initialized = false;
uint16_t prevRaw = 0;
int32_t totalTicks = 0;   // signed cumulative tick count since zero

// Function to read the raw angle from AS5600
uint16_t readAngleRaw() {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(0x0E);  // Start address for angle high byte
  if (Wire.endTransmission() != 0) return 0xFFFF; // comms error
  
  Wire.requestFrom((uint8_t)AS5600_ADDR, (uint8_t)2); // unambiguous overload
  if (Wire.available() == 2) {
    uint8_t highByte = Wire.read();
    uint8_t lowByte = Wire.read();
    return ((highByte & 0x0F) << 8) | lowByte;  // 12-bit angle
  }
  return 0xFFFF;  // error
}


// BLDC motor & driver instance
BLDCMotor motor = BLDCMotor(11);
BLDCDriver3PWM driver = BLDCDriver3PWM(9, 5, 6, 8);

// target variable
float target_velocity = 0;

// Commander
Commander command = Commander(Serial);

// === COMMAND HANDLERS ===

void doRPM(char* cmd) { 
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

void doLimit(char* cmd) { 
  command.scalar(&motor.voltage_limit, cmd); 
}

// Command handler for running motor clockwise at a specific RPM for 5 seconds
void doClockwise(char* cmd) {
  float rpm;
  command.scalar(&rpm, cmd); // Parse the RPM value from the command

  // Set target velocity in radians per second
  target_velocity = rpm * _RPM_TO_RADS;

  // Enable motor and driver
  driver.enable();
  motor.enable();

  // Run motor for 5 seconds
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

  Serial.println("Motor stopped and disabled.");
}

// Disable motor + driver (full safe idle)
void doDisable(char* cmd) {
  motor.disable();
  driver.disable();
  Serial.println("== SAFE MODE: Motor & Driver DISABLED ==");
}

// Enable motor + driver (begin open-loop control)
void doEnable(char* cmd) {
  driver.enable();
  motor.enable();
  Serial.println("== CONTROL MODE ENABLED ==");
}



void setup() {

  Serial.begin(115200);
  delay(500);

  // Wait until AS5600 is detected
  Wire.begin();  // Join I2C bus (UNO: SDA=A4, SCL=A5)
  delay(500);
  Serial.print("Scanning for AS5600 at address 0x");
  Serial.print(AS5600_ADDR, HEX);
  Serial.println("...");
  
  while (true) {
    Wire.beginTransmission(AS5600_ADDR);
    if (Wire.endTransmission() == 0) {
      Serial.println("AS5600 found!");
      break; // Exit the loop once the sensor is detected
    }
    delay(1000); // Wait a second before retrying
  }

  SimpleFOCDebug::enable(&Serial);


  // --- DRIVER SETUP ---
  driver.voltage_power_supply = 12;
  driver.voltage_limit = 6;

  if(!driver.init()){
    Serial.println("Driver init failed!");
    return;
  }

  // --- MOTOR SETUP ---
  motor.linkDriver(&driver);
  motor.voltage_limit = 6;
  motor.controller = MotionControlType::velocity_openloop;

  if(!motor.init()){
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

  // Commander commands
  command.add('R', doRPM, "target RPM");
  command.add('L', doLimit, "voltage limit");
  command.add('X', doDisable, "disable outputs (safe mode)");
  command.add('E', doEnable,  "enable motor/driver");
  command.add('C', doClockwise, "run clockwise at RPM for 5 sec");
}

void loop() {

  uint16_t raw = readAngleRaw();
  if (raw == 0xFFFF) {
    Serial.println("Read error");
    delay(200);
    return;
  }

  if (!initialized) {
    // Display the raw angle in degrees
    float rawAngleDegrees = (raw * 360.0f) / COUNTS_PER_REV;
    Serial.print("Initial Raw angle in degrees :: ");
    Serial.println(rawAngleDegrees, 2);

    // Treat first reading as zero reference: map current physical angle -> logical 0
    prevRaw = raw;
    totalTicks = 0;
    initialized = true;
    Serial.print("Zeroed at :: ");
    // Explicitly show start state as 0 rev +0.00 deg
    Serial.print("+");
    Serial.print(0);
    Serial.print(" rev +");
    Serial.print(0.00, 2);
    Serial.println(" deg");
    delay(200);
    return;
  }
  /*

  // compute delta with wrap correction
  int32_t delta = (int32_t)raw - (int32_t)prevRaw;
  if (delta > (COUNTS_PER_REV / 2)) {
    delta -= COUNTS_PER_REV;
  } else if (delta < -(COUNTS_PER_REV / 2)) {
    delta += COUNTS_PER_REV;
  }

  totalTicks += delta;
  prevRaw = raw;

  // compute integer revolutions and remaining angle (signed)
  int32_t revsInt = totalTicks / COUNTS_PER_REV;            // trunc toward zero
  int32_t remTicks = totalTicks % COUNTS_PER_REV;          // may be negative
  float remAngleDeg = (remTicks * 360.0f) / (float)COUNTS_PER_REV;

  // --- changed printing: show absolute values and direction ---
  // direction based on sign of totalTicks: '+' for forward, '-' for reverse, '0' if exactly zero
  char dir = (totalTicks > 0) ? '+' : (totalTicks < 0) ? '-' : '0';

  // absolute values
  uint32_t revsAbs = (revsInt >= 0) ? (uint32_t)revsInt : (uint32_t)(-revsInt);
  float remAngleAbs = (remAngleDeg >= 0.0f) ? remAngleDeg : -remAngleDeg;

  // print direction + absolute revolutions and absolute remaining angle
  if (dir != '0') Serial.print(dir);
  Serial.print(revsAbs);
  Serial.print(" rev ");

  if (dir != '0') Serial.print(dir);
  Serial.print(remAngleAbs, 2);
  Serial.println(" deg");
  // --- end changed printing ---
*/
  delay(5000);

  // command.run();
  // motor.move(target_velocity);

}
