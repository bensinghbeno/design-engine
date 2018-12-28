#include <SoftwareSerial.h>

String a;

// GPIO Pin Defs
const int gpioD2 = 16;
const int gpioD3 = 5;
const int gpioD4 = 4;
const int gpioD5 = 14;


// Auxiliar variables to store the current gpio state
String gpioD2State = "off";
String gpioD3State = "off";
String gpioD4State = "off";
String gpioD5State = "off";

void SetGpioHigh()
{  
              Serial.println("GPIO D2 D3 D4 D5 ON");

              digitalWrite(gpioD2, HIGH);
              digitalWrite(gpioD3, HIGH);
              digitalWrite(gpioD4, HIGH);
              digitalWrite(gpioD5, HIGH);
}

void setup() 
{
  Serial.begin(9600); 

  pinMode(gpioD2, OUTPUT);
  pinMode(gpioD3, OUTPUT);
  pinMode(gpioD4, OUTPUT);
  pinMode(gpioD5, OUTPUT);

  SetGpioHigh();
}

void loop() {

  Serial.println("Hello Android from Arduino !! .. \n");
  while(true)
  {
    delay(1000);
    Serial.println("gpioD2 D3 D4 D5, HIGH \n");

    digitalWrite(gpioD2, HIGH);
    digitalWrite(gpioD3, HIGH);
    digitalWrite(gpioD4, HIGH);
    digitalWrite(gpioD5, HIGH);
    delay(1000);
    
    Serial.println("gpioD2 D3 D4, LOW \n");
    digitalWrite(gpioD2, LOW);
    digitalWrite(gpioD3, LOW);
    digitalWrite(gpioD4, LOW);
    digitalWrite(gpioD5, LOW);
  }
}
/*
  
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
a.trim();
//
if (a.equals("FORWARD"))
{
  Serial.println("Command:  FORWARD");

              SetGpioHigh();

              Serial.println("GPIO 5 off");
              Serial.println("GPIO 3 off");

              //output4State = "off";
              output3State = "off";
              
              digitalWrite(output4, LOW);
              digitalWrite(output3, LOW);

              delay(200);
              SetGpioHigh();  
//
}
else if (a.equals("REVERSE"))
{
  Serial.println("Command:  REVERSE");

              Serial.println("GPIO 16 off");
              Serial.println("GPIO 1 off");

              output2State = "off";
              output1State = "off";
              
              digitalWrite(output2, LOW);
              digitalWrite(output1, LOW);

              delay(200);
              SetGpioHigh(); 
//
}
else if (a.equals("LEFT"))
{
  Serial.println("Command:  LEFT");
               SetGpioHigh();

              Serial.println("GPIO 16 off");
              Serial.println("GPIO 3 off");

              output2State = "off";
              output3State = "off";
              
              digitalWrite(output2, LOW);
              digitalWrite(output3, LOW);

              delay(90);
              SetGpioHigh();
//
}
else if (a.equals("RIGHT"))
{
  Serial.println("Command:  RIGHT");
               SetGpioHigh();               

              Serial.println("GPIO 1 off");
              Serial.println("GPIO 5 off");

              output1State = "off";
              output4State = "off";
              
              digitalWrite(output1, LOW);
              digitalWrite(output4, LOW);

              delay(90);
              SetGpioHigh();    
//
}
else if (a.equals("STOP"))
{
  Serial.println("Command:  STOP");
              SetGpioHigh();
//
}
else
{
  
  Serial.println("Command:  NOT Recognized");
              SetGpioHigh();

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
//}*/
