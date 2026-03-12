// DM542TE Control - Common Anode Wiring
// 1600 steps/rev | 1.1A RMS (Safe for Plastic Gearbox)

const int stepPin = 3;
const int dirPin = 2;

const int STEPS_PER_REV = 1600;
const int DIR_CW = LOW;  // Clockwise
const int DIR_ACW = HIGH; // Anti-Clockwise
const unsigned int PULSE_WIDTH_US = 10;

void setup() {
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  
  // In Common Anode, keeping pins HIGH means the internal LED is OFF
  digitalWrite(stepPin, HIGH);
  digitalWrite(dirPin, HIGH);

  Serial.begin(115200);
  Serial.println("DM542TE System Online.");
  Serial.println("Enter command: C<rpm> for Clockwise, A<rpm> for Anti-Clockwise");
  Serial.println("Example: C5 for 5 RPM Clockwise, A10 for 10 RPM Anti-Clockwise");
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();

    if (cmd.length() > 1) {
      char directionCmd = cmd.charAt(0);
      String rpmStr = cmd.substring(1);
      long rpm = rpmStr.toInt();

      if (rpm > 0) {
        int direction;
        if (directionCmd == 'C') {
          direction = DIR_CW;
          Serial.print("Moving Clockwise at ");
        } else if (directionCmd == 'A') {
          direction = DIR_ACW;
          Serial.print("Moving Anti-Clockwise at ");
        } else {
          Serial.println("Invalid direction. Use 'C' or 'A'.");
          return;
        }

        Serial.print(rpm);
        Serial.println(" RPM (1 revolution)...");

        // stepInterval is the total time for one step cycle (HIGH and LOW pulse) in microseconds
        // stepInterval = (seconds_per_minute * microseconds_per_second) / (steps_per_rev * rpm)
        // The denominator must be cast to a larger type (unsigned long) to prevent overflow during multiplication.
        // On an Arduino Uno/Nano, an 'int' is 16 bits, and `1600 * 100` already exceeds its maximum value.
        unsigned long stepInterval = (60UL * 1000000UL) / ((unsigned long)STEPS_PER_REV * rpm);

        if (stepInterval <= PULSE_WIDTH_US) {
          Serial.println("Error: RPM is too high. Resulting step interval is too short.");
          return;
        }
        moveStepper(direction, STEPS_PER_REV, stepInterval);

      } else {
        Serial.println("Invalid RPM. Must be a positive number.");
      }
    } else if (cmd.length() > 0) {
        Serial.println("Invalid command format. Example: C5");
    }
  }
}

void moveStepper(int direction, int totalSteps, unsigned long interval) {
  digitalWrite(dirPin, direction);
  delay(10); // Short delay for driver to register direction change

  for (int i = 0; i < totalSteps; i++) {
    digitalWrite(stepPin, LOW);  // PULSE START (LED ON)
    delayMicroseconds(PULSE_WIDTH_US);       // Pulse width
    digitalWrite(stepPin, HIGH); // PULSE END (LED OFF)
    delayMicroseconds(interval - PULSE_WIDTH_US); // Time until next pulse
  }
  Serial.println("Done.");
}