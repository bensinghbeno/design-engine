/**
 *
 * Position/angle motion control example
 * Steps:
 * 1) Configure the motor and magnetic sensor
 * 2) Run the code
 * 3) Set the target angle (in degrees) from serial terminal
 *
 */
#include <SimpleFOC.h>

// magnetic sensor instance - SPI
//MagneticSensorSPI sensor = MagneticSensorSPI(AS5147_SPI, 10);
// magnetic sensor instance - MagneticSensorI2C
MagneticSensorI2C sensor = MagneticSensorI2C(AS5600_I2C);
// magnetic sensor instance - analog output
// MagneticSensorAnalog sensor = MagneticSensorAnalog(A1, 14, 1020);

// BLDC motor & driver instance
BLDCMotor motor = BLDCMotor(44);
BLDCDriver3PWM driver = BLDCDriver3PWM(9, 5, 6, 8);
// Stepper motor & driver instance
//StepperMotor motor = StepperMotor(50);
//StepperDriver4PWM driver = StepperDriver4PWM(9, 5, 10, 6,  8);

// angle set point variable
float target_angle = 0;

// Timed movement variables
bool timer_active = false;
unsigned long timer_start = 0;
float target_velocity = 0;
bool is_calibrated = false;

// instantiate the commander
Commander command = Commander(Serial);
void doEnable(char* cmd) {
  motor.enable();
  // Set target to current angle to prevent snapping
  target_angle = sensor.getAngle();
  Serial.println(F("Enabled."));
  Serial.print(F("Current angle: "));
  Serial.println(sensor.getAngle() * 180.0 / PI);
}

void doDisable(char* cmd) {
  timer_active = false;
  motor.disable();
  motor.controller = MotionControlType::angle;
  Serial.println(F("Disabled."));
}

void doCW(char* cmd) {
  if (!is_calibrated) {
    motor.initFOC();
    is_calibrated = true;
    motor.controller = MotionControlType::angle;
    target_angle = sensor.getAngle();
    motor.enable();
    Serial.println(F("Calibrated. Locked."));
    Serial.print(F("Angle: "));
    Serial.println(sensor.getAngle() * 180.0 / PI);
    return;
  }
  float rpm = 50; // Default to 50 RPM if not provided
  command.scalar(&rpm, cmd);
  motor.controller = MotionControlType::velocity;
  target_velocity = abs(rpm) * _RPM_TO_RADS; // CW direction (Positive)
  timer_active = true;
  timer_start = millis();
}

void doCCW(char* cmd) {
  float rpm = 100; // Default to 100 RPM if not provided
  command.scalar(&rpm, cmd);
  motor.controller = MotionControlType::velocity;
  target_velocity = -abs(rpm) * _RPM_TO_RADS; // CCW direction (Negative)
  timer_active = true;
  timer_start = millis();
}

void setup() {

  // use monitoring with serial 
  Serial.begin(115200);
  // enable more verbose output for debugging
  // comment out if not needed
  SimpleFOCDebug::enable(&Serial);

  // initialise magnetic sensor hardware
  sensor.init();
  // increase I2C clock speed to 400kHz for better performance
  Wire.setClock(400000);
  // link the motor to the sensor
  motor.linkSensor(&sensor);

  // driver config
  // power supply voltage [V]
  driver.voltage_power_supply = 12;
  driver.init();
  // link the motor and the driver
  motor.linkDriver(&driver);

  // choose FOC modulation (optional)
  motor.foc_modulation = FOCModulationType::SpaceVectorPWM;

  // set motion control loop to be used
  motor.controller = MotionControlType::angle;

  // contoller configuration
  // default parameters in defaults.h

  // velocity PI controller parameters
  motor.PID_velocity.P = 0.5f;
  motor.PID_velocity.I = 2.0f;
  motor.PID_velocity.D = 0;
  // maximal voltage to be set to the motor
  motor.voltage_limit = 12;

  // velocity low pass filtering time constant
  // the lower the less filtered
  motor.LPF_velocity.Tf = 0.01f;

  // angle P controller
  motor.P_angle.P = 5;
  // maximal velocity of the position control
  motor.velocity_limit = 20;
  
  // comment out if not needed
  motor.useMonitoring(Serial);


  // initialize motor
  motor.init();

  // add enable command E
  command.add('E', doEnable, "enable motor");
  command.add('X', doDisable, "disable motor");
  command.add('C', doCW, "CW 5s");
  command.add('A', doCCW, "CCW 5s");

  Serial.println(F("Motor ready."));
  Serial.println(F("Motor disabled. Press 'C' to calibrate."));
  _delay(1000);
}


void loop() {

  // main FOC algorithm function
  // the faster you run this function the better
  // Arduino UNO loop  ~1kHz
  // Bluepill loop ~10kHz
  if (is_calibrated) {
    motor.loopFOC();
  }

  // Motion control function
  // velocity, position or voltage (defined in motor.controller)
  // this function can be run at much lower frequency than loopFOC() function
  // You can also use motor.move() and set the motor.target in the code
  
  if (is_calibrated) {
    if (timer_active) {
      if (millis() - timer_start > 5000) {
        timer_active = false;
        motor.controller = MotionControlType::angle;
        target_angle = sensor.getAngle(); // Hold position where it stopped
        Serial.print(F("Stopped. Angle: "));
        Serial.println(target_angle * 180.0 / PI);
      }
    }

    if (timer_active) {
      motor.move(target_velocity);
    } else {
      motor.move(target_angle);
    }
  }


  // function intended to be used with serial plotter to monitor motor variables
  // significantly slowing the execution down!!!!
  // motor.monitor();

  // user communication
  command.run();
}