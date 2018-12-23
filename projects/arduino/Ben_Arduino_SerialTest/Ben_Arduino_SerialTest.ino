#include <SoftwareSerial.h>

String a;
//const int output2 = 16;


void setup() {

Serial.begin(115200); // opens serial port, sets data rate
//Serial.println("Hello Arduino Serial\n");
//pinMode(output2, OUTPUT);
//digitalWrite(output2, LOW);


}

void loop() {

  Serial.println("Hello Android from Arduino !! .. \n");
  delay(1000);
  while(true)
  {
if(Serial.available()) {

//Serial.println("Hello Android from Arduino !! .. \n");
//
//
a= Serial.readString();// read the incoming data as string
//
//Serial.println(a);
//a.trim();
//
if (a.equals("b"))
{
  Serial.println("Command:  Recognized");
//  digitalWrite(output2, HIGH);
//
}
else
{
  
  Serial.println("Command:  NOT Recognized");

//  Serial.println("Command: Default : GPIO16 OFF ");
//  digitalWrite(output2, LOW);

}

}


}  
}

//while(Serial.available()) {
//
//Serial.println("Hello Android from Arduino !! .. \n");
//
//
//a= Serial.readString();// read the incoming data as string
//
//Serial.println(a);
//a.trim();
//
//if (a.equals("b"))
//{
//  Serial.println("Command:  GPIO16 ON ");
//  digitalWrite(output2, HIGH);
//
//}
//else
//{
//  Serial.println("Command: Default : GPIO16 OFF ");
//  digitalWrite(output2, LOW);

//}
//
//}
//
//}
