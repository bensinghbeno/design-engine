/*
L298N Pin        Connect To MKR       Description
ENA              D4                  PWM speed / enable
IN1              D2                  Motor direction 1
IN2              D3                  Motor direction 2
12V              External supply     Motor power
GND              Common ground       Must share with MKR
*/

#define L298_ENA 4
#define L298_IN1 2
#define L298_IN2 3

void setup() {
  pinMode(L298_ENA, OUTPUT);
  pinMode(L298_IN1, OUTPUT);
  pinMode(L298_IN2, OUTPUT);

  Serial.begin(115200);

  // **Do NOT print before Serial is ready**
  while (!Serial);

  Serial.println("L298 DC Gear Motor Control via Serial input in milliseconds");
}

void rotateMotor(int ms) {
  digitalWrite(L298_IN1, HIGH);
  digitalWrite(L298_IN2, LOW);
  analogWrite(L298_ENA, 255);   // Full speed

  delay(ms);

  analogWrite(L298_ENA, 0);
  digitalWrite(L298_IN1, LOW);
  digitalWrite(L298_IN2, LOW);
}

void loop() {
  if (Serial.available()) {
    int ms = Serial.parseInt();

    // Ignore zero / invalid input
    if (ms > 0) {
      Serial.print("Received Input ms: ");
      Serial.println(ms);

      rotateMotor(ms);
    }
    
    // Clear CR/LF characters
    while (Serial.available()) Serial.read();
  }
}
