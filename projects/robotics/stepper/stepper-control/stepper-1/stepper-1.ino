#include <Arduino.h> // Ensure Arduino constants and functions are defined

// Voltage Source
// 24 Volts, 2.7 A

const int stepPin = 3;
const int dirPin = 2;
const int enablePin = 4; // Pin to enable/disable the driver

const int STEPS_PER_REV = 400; // Updated to 400 for DM542TE (SW5-SW8=ON)
const int DIR_CW = LOW;
const int DIR_ACW = HIGH;
const unsigned int PULSE_WIDTH_US = 50; // Increased for better signal stability
const int GEAR_RATIO = 10; // 10:1 Gearbox integration

#define COMMAND_RUN_TIME 500 // Define the amount of milliseconds a command will run

// Set holdEnabled to true by default
bool holdEnabled = true;

const int buttonPinDirection = 7; // Button to control direction
const int buttonPinStop = 6; // Button to control start/stop
const int BUTTON_RPM = 10; // RPM for button-controlled rotation

void setup() {
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  pinMode(enablePin, OUTPUT);
  pinMode(buttonPinDirection, INPUT_PULLUP); // Enable internal pull-up resistor for pin 7
  pinMode(buttonPinStop, INPUT_PULLUP); // Enable internal pull-up resistor for pin 6
  digitalWrite(stepPin, HIGH);
  digitalWrite(dirPin, HIGH);
  digitalWrite(enablePin, HIGH); // Enable driver initially to hold the motor
  Serial.begin(115200);
  digitalWrite(enablePin, HIGH); // Enable driver (ENA- LOW) when a command is received
  delay(200); // Short delay to ensure the driver is ready
  Serial.println("Stepper Motor Control Initialized. Send commands in the format: C100 for CW at 100 RPM, A100 for ACW at 100 RPM.");
}

void loop() 
{
    int directionState = digitalRead(buttonPinDirection);
    int stopState = digitalRead(buttonPinStop);

    if (stopState == HIGH) 
    {
       digitalWrite(enablePin, LOW); // Stop rotating
    } 
    else 
    {
      digitalWrite(enablePin, HIGH); // Enable rotation

      if (directionState == HIGH) {
        Serial.println("Rotating Clockwise");
      } else {
        Serial.println("Rotating Anticlockwise");
      }

      int direction = (directionState == HIGH) ? DIR_CW : DIR_ACW;
      long motorRPM = BUTTON_RPM * GEAR_RATIO;
      unsigned long targetInterval = (60UL * 1000000UL) / ((unsigned long)STEPS_PER_REV * motorRPM);

      // Rotate at 10 RPM until the stop button is released (Pin goes HIGH)
      digitalWrite(dirPin, direction);
      while (digitalRead(buttonPinStop) == LOW) {
        digitalWrite(stepPin, LOW);
        delayMicroseconds(PULSE_WIDTH_US);
        digitalWrite(stepPin, HIGH);
        
        unsigned long pause = targetInterval - PULSE_WIDTH_US;
        // Handle potential long delays for very low RPM
        if (pause > 16000) {
          delay(pause / 1000);
          delayMicroseconds(pause % 1000);
        } else {
          delayMicroseconds(pause);
        }
      }

      Serial.println("Button released. Stopping.");
      return; 
    }
    

  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();

    if (cmd == "E") {
      holdEnabled = true;
      digitalWrite(enablePin, HIGH);
      Serial.println("HOLD ENABLED: Motor will remain engaged after command execution.");
      return;
    } else if (cmd == "X") {
      holdEnabled = false;
      digitalWrite(enablePin, LOW);
      Serial.println("HOLD DISABLED: Motor will disengage after command execution.");
      return;
    }

    if (cmd.length() > 1) {
      char directionCmd = cmd.charAt(0);
      long rpm = cmd.substring(1).toInt();

      if (rpm > 0) {
        int direction = (directionCmd == 'C') ? DIR_CW : DIR_ACW;
        long motorRPM = rpm * GEAR_RATIO;
        unsigned long targetInterval = (60UL * 1000000UL) / ((unsigned long)STEPS_PER_REV * motorRPM);

        moveTimed(direction, targetInterval, COMMAND_RUN_TIME);
      }
    }



    if (!holdEnabled) {
      digitalWrite(enablePin, LOW); // Disable driver (ENA- HIGH) after command execution
    }
  }
}

void moveTimed(int direction, unsigned long targetInterval, unsigned long durationMillis) {
  digitalWrite(dirPin, direction);
  delay(100); 

  unsigned long runTimeMicros = durationMillis * 1000UL; // Convert milliseconds to microseconds
  unsigned long startTime = micros();

  // SOFT START: Start with a slower interval (approx 4000us) to prevent jerking
  // If target is slower than start speed, just use target.
  unsigned long currentInterval = 4000; 
  if (targetInterval > currentInterval) currentInterval = targetInterval;

  while (micros() - startTime < runTimeMicros) {
    // RAMPING: Gently decrease interval (increase speed) until we hit target
    if (currentInterval > targetInterval) {
      currentInterval -= 10; // Ramping step
      if (currentInterval < targetInterval) currentInterval = targetInterval;
    }

    // Generate a slower pulse
    digitalWrite(stepPin, LOW);
    delayMicroseconds(PULSE_WIDTH_US);
    digitalWrite(stepPin, HIGH);
    
    unsigned long pause = currentInterval - PULSE_WIDTH_US;
    if ((micros() - startTime) + pause > runTimeMicros) break;
    
    // Fix: delayMicroseconds acts erratically > 16383us on standard AVR boards.
    // For low RPM (High Torque), we must use delay() for the bulk of the time.
    if (pause > 16000) {
      delay(pause / 1000);
      delayMicroseconds(pause % 1000);
    } else {
      delayMicroseconds(pause);
    }
  }
  Serial.println("Run complete.");
}