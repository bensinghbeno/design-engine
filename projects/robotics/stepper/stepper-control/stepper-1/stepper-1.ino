
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

#define COMMAND_RUN_TIME 3 // Define the amount of seconds a command will run

bool holdEnabled = false;

void setup() {
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  pinMode(enablePin, OUTPUT);
  digitalWrite(stepPin, HIGH);
  digitalWrite(dirPin, HIGH);
  digitalWrite(enablePin, LOW); // Disable driver initially to prevent motor locking
  Serial.begin(115200);
  Serial.println("32V TORQUE MODE: 400 steps/rev | Soft Start | 10:1 Gearbox");
}

void loop() {
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

    digitalWrite(enablePin, HIGH); // Enable driver (ENA- LOW) when a command is received

    if (cmd.length() > 1) {
      char directionCmd = cmd.charAt(0);
      long rpm = cmd.substring(1).toInt();

      if (rpm > 0) {
        int direction = (directionCmd == 'C') ? DIR_CW : DIR_ACW;
        long motorRPM = rpm * GEAR_RATIO;
        unsigned long targetInterval = (60UL * 1000000UL) / ((unsigned long)STEPS_PER_REV * motorRPM);

        moveTimed(direction, targetInterval);
      }
    }

    if (!holdEnabled) {
      digitalWrite(enablePin, LOW); // Disable driver (ENA- HIGH) after command execution
    }
  }
}

void moveTimed(int direction, unsigned long targetInterval) {
  digitalWrite(dirPin, direction);
  delay(100); 

  unsigned long runTimeMicros = COMMAND_RUN_TIME * 1000000UL; // Use the macro for run time
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