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

// --- Custom AS5600 Sensor Code Integration ---
const uint8_t AS5600_ADDR = 0x36;
const int COUNTS_PER_REV = 4096;

// Function to read the raw angle from AS5600
uint16_t readAngleRaw() {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(0x0E); // Address of angle register
  if (Wire.endTransmission(false) != 0) return 0xFFFF; // Use false to keep connection active

  Wire.requestFrom((uint8_t)AS5600_ADDR, (uint8_t)2);
  if (Wire.available() == 2) {
    uint8_t highByte = Wire.read();
    uint8_t lowByte = Wire.read();
    return ((highByte & 0x0F) << 8) | lowByte;
  }
  return 0xFFFF; // Error
}

// Wrapper function for SimpleFOC GenericSensor: returns angle in radians
float getSensorAngle(){
  uint16_t raw_angle = readAngleRaw();
  // Convert 12-bit raw angle (0-4095) to radians (0-2PI)
  return ( (float)raw_angle / (float)COUNTS_PER_REV ) * _2PI;
}

// Wrapper function for SimpleFOC GenericSensor: initialises the sensor
void initSensor() {
  Wire.begin(); // Init I2C
  Serial.println("Scanning for AS5600...");
  while (readAngleRaw() == 0xFFFF) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("\nAS5600 Found!");
}

// Create a GenericSensor instance using our custom functions
GenericSensor sensor = GenericSensor(getSensorAngle, initSensor);
// --- End of Custom Sensor Code ---

// BLDC motor & driver instance
BLDCMotor motor = BLDCMotor(11);
BLDCDriver3PWM driver = BLDCDriver3PWM(9, 5, 6, 8);
// Stepper motor & driver instance
//StepperMotor motor = StepperMotor(50);
//StepperDriver4PWM driver = StepperDriver4PWM(9, 5, 10, 6,  8);

// angle set point variable
float target_angle = 0;
// instantiate the commander
Commander command = Commander(Serial);
void doTarget(char* cmd) { command.scalar(&target_angle, cmd); }

// Timer for serial printing
unsigned long last_print_time = 0;
const int print_interval = 500; // ms

void setup() {

  // use monitoring with serial 
  Serial.begin(115200);
  // enable more verbose output for debugging
  // comment out if not needed
  SimpleFOCDebug::enable(&Serial);
  
  // initialise magnetic sensor hardware
  sensor.init(); // This will call our custom initSensor() function
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
  motor.PID_velocity.P = 0.2f;
  motor.PID_velocity.I = 20;
  motor.PID_velocity.D = 0;
  // maximal voltage to be set to the motor
  motor.voltage_limit = 6;

  // velocity low pass filtering time constant
  // the lower the less filtered
  motor.LPF_velocity.Tf = 0.01f;

  // angle P controller
  motor.P_angle.P = 20;
  // maximal velocity of the position control
  motor.velocity_limit = 20;
  
  // comment out if not needed
  motor.useMonitoring(Serial);


  // initialize motor
  motor.init();
  
  // Set a higher voltage for sensor alignment. (Default is 1V)
  motor.voltage_sensor_align = 3; // Volts

  // align sensor and start FOC
  motor.initFOC(); // This will now use 3V for alignment

  // add target command T
  command.add('T', doTarget, "target angle");

  Serial.println(F("Motor ready."));
  Serial.println(F("Set the target angle using serial terminal:"));
  _delay(1000);
}


void loop() {

  // main FOC algorithm function
  // the faster you run this function the better
  // Arduino UNO loop  ~1kHz
  // Bluepill loop ~10kHz
  motor.loopFOC(); // This calls getSensorAngle() internally

  // Motion control function
  // velocity, position or voltage (defined in motor.controller)
  // this function can be run at much lower frequency than loopFOC() function
  // You can also use motor.move() and set the motor.target in the code
  motor.move(target_angle);


  // user communication
  command.run();

  // Print status periodically
  if (millis() - last_print_time > print_interval) {
    last_print_time = millis();
    Serial.print(F("Target: "));
    Serial.print(target_angle, 2); // Print with 2 decimal places
    Serial.print(F("\t Current: "));
    Serial.println(motor.shaft_angle, 2); // shaft_angle is the current motor angle
  }
}