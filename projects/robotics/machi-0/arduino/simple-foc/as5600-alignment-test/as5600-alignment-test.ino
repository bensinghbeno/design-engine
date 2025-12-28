// Test code for AS5600 sensor feedback
#include <SimpleFOC.h>
#include <Wire.h>

// Magnetic sensor instance
MagneticSensorI2C sensor = MagneticSensorI2C(AS5600_I2C);

// BLDC motor & driver instance
BLDCMotor motor = BLDCMotor(4); // 4 pole pairs
BLDCDriver3PWM driver = BLDCDriver3PWM(9, 5, 6, 8);

// Target variable
float target_velocity = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Wire.begin();
  delay(500);

  Serial.println("AS5600 Sensor Feedback Test");

  // Initialize the sensor
  sensor.init();
  Serial.println("Sensor initialized.");

  // Link the motor to the sensor
  motor.linkSensor(&sensor);

  // Driver setup
  driver.voltage_power_supply = 12;
  driver.init();
  motor.linkDriver(&driver);

  // Motor setup
  motor.voltage_limit = 6;
  motor.controller = MotionControlType::velocity_openloop;
  motor.init();

  Serial.println("Motor and driver initialized.");
}

unsigned long last_log_time = 0;

void loop() {
  unsigned long current_time = millis();
  if (current_time - last_log_time >= 4000) { // Log every 4 seconds
    last_log_time = current_time;

    // Read sensor angle
    float sensor_angle = sensor.getAngle();

    // Log the sensor angle
    Serial.print("Sensor angle: ");
    Serial.print(sensor_angle * 180.0 / PI, 3);
    Serial.println(" degrees");
  }

  // Move motor in open-loop mode
  motor.move(target_velocity);
}