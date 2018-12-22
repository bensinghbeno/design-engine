#include <SoftwareSerial.h>

String a;
const int output2 = 16;


void setup() {

Serial.begin(115200); // opens serial port, sets data rate
Serial.println("Hello Arduino Serial\n");
pinMode(output2, OUTPUT);
digitalWrite(output2, LOW);


}

void loop() {

while(Serial.available()) {

a= Serial.readString();// read the incoming data as string

Serial.println(a);
//a.trim();

if (a.equals("b"))
{
  Serial.println("Command:  GPIO16 ON ");
  digitalWrite(output2, HIGH);

}
else
{
  Serial.println("Command: Default : GPIO16 OFF ");
  digitalWrite(output2, LOW);

}

}

}
