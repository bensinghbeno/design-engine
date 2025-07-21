void setup() {
  Serial.begin(9600);       // Start serial communication at 9600 baud
  Serial.println("Hello, World!"); // Print once on startup
}

void loop() {
  if (Serial.available() > 0) {           // If input is available
    String input = Serial.readString();   // Read the full input
    Serial.print("You typed: ");          // Echo response
    Serial.println(input);
  }
}