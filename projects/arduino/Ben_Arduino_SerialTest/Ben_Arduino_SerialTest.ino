#include <SoftwareSerial.h>

SoftwareSerial mySerial(9, 10); // RX, TX

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }


  Serial.println("Arduino Serial Connected!");

  // set the data rate for the SoftwareSerial port
  mySerial.begin(115200);
  while (!mySerial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.println("Software Serial Connected!!");

  mySerial.println("AT\r\n");
}

void loop() { // run over and over
  delay(500);
    mySerial.write("AT\r\n");

  if (mySerial.available()) {
    Serial.write(mySerial.read());
  }
  if (Serial.available()) {
    mySerial.write(Serial.read());
  }
}
