// Open loop motor control example - SAFE MODE VERSION
#include <SimpleFOC.h>

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
}

void doLimit(char* cmd) { 
  command.scalar(&motor.voltage_limit, cmd); 
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
}

void loop() {

  // Only move if motor is enabled
  // (motor.disable() automatically blocks torque output)
  motor.move(target_velocity);

  command.run();
}
