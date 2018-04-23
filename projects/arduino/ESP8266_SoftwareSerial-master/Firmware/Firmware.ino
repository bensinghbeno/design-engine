/*  Robo-Plan Technologies LTD: 08/2016

   The purpose of this Arduino Sketch is to check the ESP8266-01 as a peripheral wifi board connected to
   an Arduino Uno board via a 5-3.3 logic converter with SoftwareSerial using ESP8266 AT command library created by ITEAD.
   
   The original library can be found: https://github.com/itead/ITEADLIB_Arduino_WeeESP8266

   Our goal was to create an Esp8266 AT command library (based on ITEAD library), 
   that would work well on software serial on most ESP8266 devices, no matter the firmware, or the initial baudrate.
   
   Therefore, we are distributing this preliminary library. Please connect the Esp8266-01 and run this example.
   Write to us about any bugs, comments, issues, improvement proposals, etc.

   We have modified the original library due to Software serial baudrate problems.
   Now, the initialize function, when using software serial only, will set the ESP8266 baudrate to 9600.
   
   The sketch sets the ESP8266 baudrate to 9600 by default for software serial and to 115200 with hardware serial. 
   Then it connects to your AP, checks the version of the ESP8266, sends a TCP request to google.com and displays the response on the serial monitor.

   Notes:
   -  In order to run the example, first connect the ESP8266 via Software Serial to your arduino board using a logic converter,
        as shown in the wiring figure attached.
   -  Enter your SSID and PASSWORD below.
   -  If using SoftwareSerial make sure the line "#define ESP8266_USE_SOFTWARE_SERIAL" in ESP8266.h is uncommented.


 Troubleshooting:
   -  If you receive partial response from the esp8266 when using software serial - 
      go to C:\Program Files (x86)\Arduino\hardware\arduino\avr\libraries\SoftwareSerial\src\SoftwareSerial.h
      Change line 42: #define _SS_MAX_RX_BUFF 64 // RX buffer size
      To: #define _SS_MAX_RX_BUFF 256 // RX buffer size
      this will enlarge the software serial buffer.
   -  Sometime setting the baudrate on initialization fails, try resetting the Arduino, it should work fine.
   
*/

#include "ESP8266.h"

void getReply(int wait);


const char *SSID     = "Yuvaraj";
const char *PASSWORD = "9994208118";
const bool printReply = true;
const char line[] = "-----\n\r";
int loopCount=0;
 
char html[50];
char command[20];
char reply[500]; // you wouldn't normally do this
 
char ipAddress [20];
char name[30];
int lenHtml = 0;
char temp[5];
 

SoftwareSerial espSerial(10, 11); //SoftwareSerial pins for MEGA/Uno. For other boards see: https://www.arduino.cc/en/Reference/SoftwareSerial

ESP8266 wifi(espSerial, 115200); 

void setup(void)
{
  //Start Serial Monitor at any BaudRate
  Serial.begin(57600);
  Serial.println("Begin");

  Serial.println("reset the module"); 
  espSerial.print("AT\n");
  getReply( 10000 );

  /*if (!wifi.init(SSID, PASSWORD))
  {
    Serial.println("Wifi Init failed. Check configuration.");
    while (true) ; // loop eternally
  }*/
}


void loop(void)
{   
    Serial.println("Sending Request to www.google.com");
    //wifi.httpGet();

    delay(4000);
}

void getReply(int wait)
{
    int tempPos = 0;
    long int time = millis();
    while( (time + wait) > millis())
    {
        while(espSerial.available())
        {
            char c = espSerial.read(); 
            if (tempPos < 500) { reply[tempPos] = c; tempPos++;   }
        }
        reply[tempPos] = 0;
    } 
 
    if (printReply) { Serial.println( reply );  Serial.println(line);     }
}







