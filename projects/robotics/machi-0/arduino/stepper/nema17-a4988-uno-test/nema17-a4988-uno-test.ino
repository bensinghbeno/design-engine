/*
Wikwi Diagram:
{
  "version": 1,
  "author": "Gemini",
  "editor": "wokwi",
  "parts": [
    { "type": "wokwi-arduino-uno", "id": "uno", "top": 67.8, "left": -125.4, "attrs": {} },
    { "type": "wokwi-a4988", "id": "driver", "top": 91.2, "left": 312, "attrs": {} },
    {
      "type": "wokwi-vcc",
      "id": "v12",
      "top": 10.36,
      "left": 355.2,
      "attrs": { "voltage": "12" }
    },
    { "type": "wokwi-stepper-motor", "id": "motor", "top": -216.29, "left": 384.88, "attrs": {} }
  ],
  "connections": [
    [ "uno:GND.1", "driver:GND.1", "black", [ "v105.6", "h374.55" ] ],
    [ "uno:5V", "driver:VDD", "limegreen", [ "v0" ] ],
    [ "uno:3", "driver:STEP", "blue", [ "v0" ] ],
    [ "uno:4", "driver:DIR", "orange", [ "v0" ] ],
    [ "driver:RESET", "driver:SLEEP", "green", [ "h-10", "v-10", "h10" ] ],
    [ "driver:EN", "uno:GND.1", "black", [ "v10" ] ],
    [ "v12:VCC", "driver:VMOT", "red", [ "v0" ] ],
    [ "driver:1A", "motor:A+", "black", [ "h124.95", "v-115.12" ] ],
    [ "driver:1B", "motor:A-", "green", [ "h115.35", "v-124.72" ] ],
    [ "driver:2A", "motor:B+", "red", [ "h134.55", "v-105.52" ] ],
    [ "driver:2B", "motor:B-", "blue", [ "h144.15", "v-95.92" ] ]
  ],
  "dependencies": {}
}

*/



// Define pin connections
const int enablePin = 2;
const int stepPin = 3;
const int dirPin = 4;

// Forward declaration
void stepMotor(int steps);

// Simple Serial Command Handler
class CommandHandler {
  struct Cmd {
    char key;
    void (*func)();
  };
  Cmd commands[10];
  int count = 0;

public:
  void add(const char* name, void (*func)()) {
    if (count < 10) {
      commands[count].key = name[0];
      commands[count].func = func;
      count++;
    }
  }

  void process() {
    if (Serial.available() > 0) {
      char c = Serial.peek();
      if (c == '\n' || c == '\r' || c == ' ') { Serial.read(); return; }
      
      char cmd = Serial.read();
      for (int i = 0; i < count; i++) {
        if (toupper(cmd) == toupper(commands[i].key)) {
          commands[i].func();
          return;
        }
      }
    }
  }
};

CommandHandler command;

void moveClockwise() {
  int steps = Serial.parseInt();
  Serial.print("Rotating Clockwise: ");
  Serial.println(steps);
  digitalWrite(dirPin, HIGH);
  stepMotor(steps);
}

void moveAntiClockwise() {
  int steps = Serial.parseInt();
  Serial.print("Rotating Anti-clockwise: ");
  Serial.println(steps);
  digitalWrite(dirPin, LOW);
  stepMotor(steps);
}

void enableDriver() {
  digitalWrite(enablePin, LOW);
  Serial.println("Driver Enabled");
}

void disableDriver() {
  digitalWrite(enablePin, HIGH);
  Serial.println("Driver Disabled (Zero Current)");
}

void setup() {
  // Initialize Enable pin first to ensure it starts disabled
  digitalWrite(enablePin, HIGH); // Set HIGH (Disabled) before setting as output
  pinMode(enablePin, OUTPUT);
  
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);

  // Initialize Serial Monitor
  Serial.begin(115200);
  Serial.println("System Ready.");
  Serial.println("Enter command (e.g., E to Enable, C100 to Move, X to Disable):");

  // 5. Setup Serial Commands 
  command.add("C", moveClockwise);
  command.add("A", moveAntiClockwise);
  command.add("E", enableDriver);
  command.add("X", disableDriver);
}

void loop() {
  command.process();
}

// Helper function to generate step pulses
void stepMotor(int steps) {
  for (int i = 0; i < steps; i++) {
    digitalWrite(stepPin, HIGH);
    delay(15); // 15ms HIGH. Total 30ms per step gives ~10 RPM
    digitalWrite(stepPin, LOW);
    delay(15); // 15ms LOW
  }
}
