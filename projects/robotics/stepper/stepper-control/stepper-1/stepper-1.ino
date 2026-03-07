// DM542TE Control - Common Anode Wiring
// 1600 steps/rev | 1.1A RMS (Safe for Plastic Gearbox)

const int stepPin = 3; 
const int dirPin = 2; 

// 5 RPM calculation for 1600 microstepping:
// Total steps per minute = 1600 * 5 = 8000
// Steps per second = 8000 / 60 = 133.33
// Microseconds per step cycle = 1,000,000 / 133.33 = 7500us
const unsigned long stepInterval = 7500; 

void setup() {
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  
  // In Common Anode, keeping pins HIGH means the internal LED is OFF
  digitalWrite(stepPin, HIGH);
  digitalWrite(dirPin, HIGH);

  Serial.begin(115200);
  Serial.println("DM542TE System Online.");
  Serial.println("1 = Forward (5 RPM) | 2 = Reverse (5 RPM)");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    if (cmd == '1') {
      Serial.println("Moving FWD...");
      moveStepper(LOW, 1600); // LOW/HIGH sets direction
    } 
    else if (cmd == '2') {
      Serial.println("Moving REV...");
      moveStepper(HIGH, 1600);
    }
  }
}

void moveStepper(int direction, int totalSteps) {
  digitalWrite(dirPin, direction);
  delay(10); // Short delay for driver to register direction change

  for (int i = 0; i < totalSteps; i++) {
    digitalWrite(stepPin, LOW);  // PULSE START (LED ON)
    delayMicroseconds(10);       // Pulse width
    digitalWrite(stepPin, HIGH); // PULSE END (LED OFF)
    delayMicroseconds(stepInterval);
  }
  Serial.println("Done.");
}