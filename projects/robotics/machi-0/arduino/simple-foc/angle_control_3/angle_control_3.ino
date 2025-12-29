/**
 *
 * Position/angle motion control example
 * Steps:
 * 1) Configure the motor and magnetic sensor
 * 2) Run the code
 * 3) Set the target angle (in radians) from serial terminal
 *
 */
#include <SimpleFOC.h>

#include <Wire.h>

// magnetic sensor instance - MagneticSensorI2C (AS5600)
const uint8_t AS5600_ADDR = 0x36;
MagneticSensorI2C sensor = MagneticSensorI2C(AS5600_I2C);

// BLDC motor & driver instance
BLDCMotor motor = BLDCMotor(44);
BLDCDriver3PWM driver = BLDCDriver3PWM(9, 5, 6, 8);
// Stepper motor & driver instance
//StepperMotor motor = StepperMotor(50);
//StepperDriver4PWM driver = StepperDriver4PWM(9, 5, 10, 6,  8);

// angle set point variable
float target_angle = 0;
// instantiate the commander
Commander command = Commander(Serial);
void doTarget(char* cmd) { command.scalar(&target_angle, cmd); }

// Helper function to replace delay() since Timer0 is used by PWM on pins 5 & 6
void delay_safe(unsigned long ms)
{
  for (unsigned long i = 0; i < ms; i++)
  {
    delayMicroseconds(1000);
  }
}

void setup() {

  // use monitoring with serial 
  Serial.begin(115200);

  // Wait until AS5600 is detected (from reference code)
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

  // enable more verbose output for debugging
  // comment out if not needed
  SimpleFOCDebug::enable(&Serial);

  // initialise magnetic sensor hardware
  sensor.init();
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
  motor.PID_velocity.P = 0.05f; // Reduced for stability
  motor.PID_velocity.I = 1.0f;  // Reduced for stability
  motor.PID_velocity.D = 0;
  // maximal voltage to be set to the motor
  motor.voltage_limit = 6;

  // velocity low pass filtering time constant
  // the lower the less filtered
  motor.LPF_velocity.Tf = 0.05f; // Increased filtering for I2C noise

  // angle P controller
  motor.P_angle.P = 1.0f; // Reduced to prevent oscillation
  // maximal velocity of the position control
  motor.velocity_limit = 0.1f; // ~1 RPM (0.1 rad/s) max speed
  
  // comment out if not needed
  motor.useMonitoring(Serial);

  // Reduce alignment voltage to prevent brownouts (reset) during init
  motor.voltage_sensor_align = 1.0; // Try 1V or 2V

  // initialize motor
  motor.init();
  // align sensor and start FOC
  motor.initFOC();

  // Start at the current angle to avoid immediate snapping to 0
  target_angle = motor.shaft_angle;

  // add target command T
  command.add('T', doTarget, "target angle");

  Serial.println(F("Motor ready."));
  Serial.println(F("Set the target angle using serial terminal:"));
  delay_safe(1000);
}


void loop() {

  // main FOC algorithm function
  // the faster you run this function the better
  // Arduino UNO loop  ~1kHz
  // Bluepill loop ~10kHz
  motor.loopFOC();

  // Motion control function
  // velocity, position or voltage (defined in motor.controller)
  // this function can be run at much lower frequency than loopFOC() function
  // You can also use motor.move() and set the motor.target in the code
  motor.move(target_angle);


  // function intended to be used with serial plotter to monitor motor variables
  // significantly slowing the execution down!!!!
  // motor.monitor();

  // user communication
  command.run();
}