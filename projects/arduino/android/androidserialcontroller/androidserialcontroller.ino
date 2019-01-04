#include <SoftwareSerial.h>

String inputCommand;

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

void setDelayedGpioHigh()
{  
              //Serial.println("GPIO D2 D3 D4 D5 ON");
  delay(50);


              digitalWrite(gpioD2, HIGH);
              digitalWrite(gpioD3, HIGH);
              digitalWrite(gpioD4, HIGH);
              digitalWrite(gpioD5, HIGH);
}

void setup() 
{
  Serial.begin(115200); 

  pinMode(gpioD2, OUTPUT);
  pinMode(gpioD3, OUTPUT);
  pinMode(gpioD4, OUTPUT);
  pinMode(gpioD5, OUTPUT);

  setDelayedGpioHigh();

  Serial.println("Hello Android from Arduino !! .. waiting for user input command \n");
}

void loop()
{
  //delay(1000);
  if(Serial.available())
  {
    inputCommand = Serial.readString();
    //inputCommand.trim();

  
    if (inputCommand.equals("FORWARD"))
    {
      //Serial.println("Command:  FORWARD");

      digitalWrite(gpioD2, HIGH);
      digitalWrite(gpioD3, LOW);
      
      digitalWrite(gpioD4, HIGH);
      digitalWrite(gpioD5, LOW);

      //Serial.println("GPIO D2 D4 ON");

      setDelayedGpioHigh();  
    }
    else if (inputCommand.equals("REVERSE"))
    {
      //Serial.println("Command:  REVERSE");

      digitalWrite(gpioD2, LOW);
      digitalWrite(gpioD3, HIGH);
      digitalWrite(gpioD4, LOW);
      digitalWrite(gpioD5, HIGH);

      //Serial.println("GPIO D3 D5 ON");
  
      setDelayedGpioHigh();  
    }
    else if (inputCommand.equals("LEFT"))
    {
      //Serial.println("Command:  LEFT");

      digitalWrite(gpioD2, HIGH);
      digitalWrite(gpioD3, LOW);
      digitalWrite(gpioD4, LOW);
      digitalWrite(gpioD5, HIGH);

      //Serial.println("GPIO D2 D5 ON");
  
      setDelayedGpioHigh();  
    }
    else if (inputCommand.equals("RIGHT"))
    {
      //Serial.println("Command:  RIGHT");

      digitalWrite(gpioD2, LOW);
      digitalWrite(gpioD3, HIGH);
      digitalWrite(gpioD4, HIGH);
      digitalWrite(gpioD5, LOW);

      //Serial.println("GPIO D3 D4 ON");
  
      setDelayedGpioHigh();  
    }
    else
    {
      Serial.print(" ERROR -");
      Serial.println(inputCommand);
      setDelayedGpioHigh();  
    }    
  }

}
