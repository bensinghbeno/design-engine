#include <IBusBM.h>

IBusBM ibus; // Create the IBUS object

void setup() {
  Serial.begin(115200);    // For Serial Monitor output
  ibus.begin(Serial1);     // iBUS receiver signal on Serial1 RX (Pin 19)
}

void loop() {
  // Read and print channel values (first 8 channels)
  for (byte i = 0; i < 8; i++) {
    int value = ibus.readChannel(i); // Get channel value (range: 1000–2000)
    Serial.print("Ch");
    Serial.print(i + 1);
    Serial.print(": ");
    Serial.print(value);
    Serial.print(" | ");
  }
  Serial.println();
  delay(100);
}
