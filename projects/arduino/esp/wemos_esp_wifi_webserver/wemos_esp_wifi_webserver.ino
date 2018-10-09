
// Load Wi-Fi library
#include <ESP8266WiFi.h>

// Replace with your network credentials
const char WiFiAPPSK[] = "4viewworld@123";


// Set web server port number to 80
WiFiServer server(80);

// Variable to store the HTTP request
String header;
String gpsData;
String gpsDataLatitude;
String gpsDataLongitude;
String accelX;
String accelY;
String accelZ;

// Auxiliar variables to store the current output state
String output2State = "off";
String output4State = "off";
String output1State = "off";
String output3State = "off";

String output5State = "off";
String output6State = "off";
String output7State = "off";
String output8State = "off";

// Assign output variables to GPIO pins (upwards from bottom right for wemos d1 pins - [3, 1, 16, 5] [4, 14, 12, 13]) 
const int output3 = 3;
const int output1 = 1;
const int output2 = 16;
const int output4 = 5;

const int output5 = 4;
const int output6 = 14;
const int output7 = 12;
const int output8 = 13;


String getValue(String data, char separator, int index)
{
    int found = 0;
    int strIndex[] = { 0, -1 };
    int maxIndex = data.length() - 1;

    for (int i = 0; i <= maxIndex && found <= index; i++) {
        if (data.charAt(i) == separator || i == maxIndex) {
            found++;
            strIndex[0] = strIndex[1] + 1;
            strIndex[1] = (i == maxIndex) ? i+1 : i;
        }
    }
    return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

void setupWiFi()
{
  WiFi.mode(WIFI_AP);

  // Do a little work to get a unique-ish name. Append the
  // last two bytes of the MAC (HEX'd) to "Thing-":
  uint8_t mac[WL_MAC_ADDR_LENGTH];
  WiFi.softAPmacAddress(mac);
  String macID = String(mac[WL_MAC_ADDR_LENGTH - 2], HEX) +
                 String(mac[WL_MAC_ADDR_LENGTH - 1], HEX);
  macID.toUpperCase();
  String AP_NameString = "4ViewWebServer";

  char AP_NameChar[AP_NameString.length() + 1];
  memset(AP_NameChar, 0, AP_NameString.length() + 1);

  for (int i=0; i<AP_NameString.length(); i++)
    AP_NameChar[i] = AP_NameString.charAt(i);

  WiFi.softAP(AP_NameChar, WiFiAPPSK);
}

void setup() {
  Serial.begin(115200);
  // Initialize the output variables as outputs
  pinMode(output2, OUTPUT);
  pinMode(output4, OUTPUT);
  pinMode(output1, OUTPUT);
  pinMode(output3, OUTPUT);

  pinMode(output5, OUTPUT);
  pinMode(output6, OUTPUT);
  pinMode(output7, OUTPUT);
  pinMode(output8, OUTPUT);

  // Set outputs to LOW
  SetGpioHigh();

  // Connect to Wi-Fi network with SSID and password
  setupWiFi();
  Serial.println("Waiting for client to connect !!");

  server.begin();

}

void SetGpioHigh()
{  
              Serial.println("GPIO 16 ON");
              Serial.println("GPIO 5 ON");
              Serial.println("GPIO 3 ON");
              Serial.println("GPIO 1 ON");  

              Serial.println("GPIO 4 ON");
              Serial.println("GPIO 14 ON");
              Serial.println("GPIO 12 ON");
              Serial.println("GPIO 13 ON");       
             
              output2State = "on";
              output4State = "on";
              output3State = "on";
              output1State = "on";

              output5State = "on";
              output6State = "on";
              output7State = "on";
              output8State = "on";
              
              
              digitalWrite(output2, HIGH);
              digitalWrite(output4, HIGH);
              digitalWrite(output3, HIGH);
              digitalWrite(output1, HIGH);

              digitalWrite(output5, HIGH);
              digitalWrite(output6, HIGH);
              digitalWrite(output7, HIGH);
              digitalWrite(output8, HIGH);
}

void loop(){
  WiFiClient client = server.available();   // Listen for incoming clients

  if (client) {
      // Print local IP address and start web server
      Serial.println("....");
      Serial.println("WiFi connected.");
      Serial.println("IP address: ");
      Serial.println(WiFi.localIP());
      //server.begin();

      // If a new client connects,
    Serial.println("New Client.");          // print a message out in the serial port
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      if (client.available()) {             // if there's bytes to read from the client,
        char c = client.read();             // read a byte, then
        Serial.write(c);                    // print it out the serial monitor
        header += c;
        if (c == '\n') {                    // if the byte is a newline character
          // if the current line is blank, you got two newline characters in a row.
          // that's the end of the client HTTP request, so send a response:
          if (currentLine.length() == 0) {
            // HTTP headers always start with a response code (e.g. HTTP/1.1 200 OK)
            // and a content-type so the client knows what's coming, then a blank line:
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html");
            client.println("Connection: close");
            client.println();

            if (header.indexOf("GET /GRAB") >= 0)
            {
              Serial.println("GPIO 4 on");
              Serial.println("GPIO 14 off");

              output5State = "on";
              output6State = "off";
              
              digitalWrite(output5, HIGH);
              digitalWrite(output6, LOW);

              delay(20);
              SetGpioHigh();              
            }
            else if (header.indexOf("GET /RELEASE") >= 0)
            {
              Serial.println("GPIO 4 off");
              Serial.println("GPIO 14 on");

              output5State = "off";
              output6State = "on";
              
              digitalWrite(output5, LOW);
              digitalWrite(output6, HIGH);

              delay(20);
              SetGpioHigh();              
            }
            else if (header.indexOf("GET /TO") >= 0)
            {
              Serial.println("GPIO 12 off");
              Serial.println("GPIO 13 on");

              output7State = "off";
              output8State = "on";
              
              digitalWrite(output7, LOW);
              digitalWrite(output8, HIGH);

              delay(20);
              SetGpioHigh();              
            }            
            else if (header.indexOf("GET /FRO") >= 0)
            {
              Serial.println("GPIO 12 on");
              Serial.println("GPIO 13 off");

              output7State = "on";
              output8State = "off";
              
              digitalWrite(output7, HIGH);
              digitalWrite(output8, LOW);

              delay(20);
              SetGpioHigh();              
            }   
            else if (header.indexOf("GET /BACK") >= 0)
            {
              Serial.println("GPIO 16 off");
              Serial.println("GPIO 1 off");

              output2State = "off";
              output1State = "off";
              
              digitalWrite(output2, LOW);
              digitalWrite(output1, LOW);

              delay(200);
              SetGpioHigh();              
            }
            else if (header.indexOf("GET /FORWARD") >= 0)
            {
              SetGpioHigh();

              Serial.println("GPIO 5 off");
              Serial.println("GPIO 3 off");

              output4State = "off";
              output3State = "off";
              
              digitalWrite(output4, LOW);
              digitalWrite(output3, LOW);

              delay(200);
              SetGpioHigh();              
            }
            else if (header.indexOf("GET /RIGHT") >= 0)
            {
              SetGpioHigh();               

              Serial.println("GPIO 1 off");
              Serial.println("GPIO 5 off");

              output1State = "off";
              output4State = "off";
              
              digitalWrite(output1, LOW);
              digitalWrite(output4, LOW);

              delay(90);
              SetGpioHigh();              
            }   
            else if (header.indexOf("GET /LEFT") >= 0)
            {
              SetGpioHigh();

              Serial.println("GPIO 16 off");
              Serial.println("GPIO 3 off");

              output2State = "off";
              output3State = "off";
              
              digitalWrite(output2, LOW);
              digitalWrite(output3, LOW);

              delay(90);
              SetGpioHigh();

            }                                     
            else if (header.indexOf("GET /STOP") >= 0)
            {
              SetGpioHigh();
            }

            // turns the GPIOs on and off
            if (header.indexOf("GET /GPS") >= 0)
            {
              Serial.println("RECEIVE GPS DATA :: ");
              Serial.println("HEADER = " + header);
              String val = "";
              for( int i = 0; i < 10 ; ++i)
              {
                val = getValue(header, '-', i);
                Serial.println("Value at : " + String(i) + " = " + val);
                if (i == 1)
                {
                  gpsDataLatitude = val;
                }
                else if (i == 2)
                {
                  gpsDataLongitude = val;
                }
                if(val == "FIN")
                {
                    break;
                }
              }                         
            }
            else if (header.indexOf("GET /ACCEL") >= 0)
            {
              Serial.println("RECEIVE ACCELEROMETER DATA :: ");
              Serial.println("HEADER = " + header);
              String val = "";
              for( int i = 0; i < 10 ; ++i)
              {
                val = getValue(header, '-', i);
                Serial.println("Value at : " + String(i) + " = " + val);
                if (i == 1)
                {
                  accelX = val;
                }
                else if (i == 2)
                {
                  accelY = val;
                }
                else if (i == 3)
                {
                  accelZ = val;
                }
                if(val == "FIN")
                {
                    break;
                }
              }                         
            }
            else if (header.indexOf("GET /16/on") >= 0) {
              Serial.println("GPIO 16 on");
              output2State = "on";
              digitalWrite(output2, HIGH);
            } else if (header.indexOf("GET /16/off") >= 0) {
              Serial.println("GPIO 16 off");
              output2State = "off";
              digitalWrite(output2, LOW);
            } else if (header.indexOf("GET /5/on") >= 0) {
              Serial.println("GPIO 5 on");
              output4State = "on";
              digitalWrite(output4, HIGH);
            } else if (header.indexOf("GET /5/off") >= 0) {
              Serial.println("GPIO 5 off");
              output4State = "off";
              digitalWrite(output4, LOW);
            } else if (header.indexOf("GET /1/on") >= 0) {
              Serial.println("GPIO 1 on");
              output1State = "on";
              digitalWrite(output1, HIGH);
            } else if (header.indexOf("GET /1/off") >= 0) {
              Serial.println("GPIO 1 off");
              output1State = "off";
              digitalWrite(output1, LOW);
            } else if (header.indexOf("GET /3/on") >= 0) {
              Serial.println("GPIO 3 on");
              output3State = "on";
              digitalWrite(output3, HIGH);
            } else if (header.indexOf("GET /3/off") >= 0) {
              Serial.println("GPIO 3 off");
              output3State = "off";
              digitalWrite(output3, LOW);
            } else if (header.indexOf("GET /4/on") >= 0) {
              Serial.println("GPIO 4 on");
              output5State = "on";
              digitalWrite(output5, HIGH);
            } else if (header.indexOf("GET /4/off") >= 0) {
              Serial.println("GPIO 4 off");
              output5State = "off";
              digitalWrite(output5, LOW);
            } else if (header.indexOf("GET /14/on") >= 0) {
              Serial.println("GPIO 14 on");
              output6State = "on";
              digitalWrite(output6, HIGH);
            } else if (header.indexOf("GET /14/off") >= 0) {
              Serial.println("GPIO 14 off");
              output6State = "off";
              digitalWrite(output6, LOW);
            } else if (header.indexOf("GET /12/on") >= 0) {
              Serial.println("GPIO 12 on");
              output7State = "on";
              digitalWrite(output7, HIGH);
            } else if (header.indexOf("GET /12/off") >= 0) {
              Serial.println("GPIO 12 off");
              output7State = "off";
              digitalWrite(output7, LOW);
            } else if (header.indexOf("GET /13/on") >= 0) {
              Serial.println("GPIO 13 on");
              output8State = "on";
              digitalWrite(output8, HIGH);
            } else if (header.indexOf("GET /13/off") >= 0) {
              Serial.println("GPIO 13 off");
              output8State = "off";
              digitalWrite(output8, LOW);
            }
            
            

            // Display the HTML web page
            client.println("<!DOCTYPE html><html>");
            client.println("<head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
            client.println("<link rel=\"icon\" href=\"data:,\">");
            // CSS to style the on/off buttons
            // Feel free to change the background-color and font-size attributes to fit your preferences
            client.println("<style>html { font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center;}");
            client.println(".button { background-color: #77878A; border: none; color: white; padding: 16px 40px;");
            client.println("text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}");
            client.println(".button2 {background-color: #195B6A;}</style></head>");

            // Web Page Heading
            client.println("<body><h1>ForeView ESP8266 Web Server</h1>");
            client.println("<body><h2>GPS Latitude  : " + gpsDataLatitude +" </h2>");
            client.println("<body><h2>GPS Longitude : " + gpsDataLongitude +" </h2>");
            client.println("<body><h2>============================================== </h2>");
            client.println("<body><h2>ACCELEROMETER X : " + accelX +" </h2>");
            client.println("<body><h2>ACCELEROMETER Y : " + accelY +" </h2>");
            client.println("<body><h2>ACCELEROMETER Z : " + accelZ +" </h2>");

            // Display current state, and ON/OFF buttons for GPIO 16
            client.println("<p>GPIO 16 - State " + output2State + "</p>");
            // If the output2State is off, it displays the ON button
            if (output2State=="off") {
              client.println("<p><a href=\"/16/on\"><button class=\"button\">OFF</button></a></p>");
            } else {
              client.println("<p><a href=\"/16/off\"><button class=\"button button2\">ON</button></a></p>");
            }

            // Display current state, and ON/OFF buttons for GPIO 5
            client.println("<p>GPIO 5 - State " + output4State + "</p>");
            // If the output4State is off, it displays the ON button
            if (output4State=="off") {
              client.println("<p><a href=\"/5/on\"><button class=\"button\">OFF</button></a></p>");
            } else {
              client.println("<p><a href=\"/5/off\"><button class=\"button button2\">ON</button></a></p>");
            }

            // Display current state, and ON/OFF buttons for GPIO 1
            client.println("<p>GPIO 1 - State " + output1State + "</p>");
            // If the output1State is off, it displays the ON button
            if (output1State=="off") {
              client.println("<p><a href=\"/1/on\"><button class=\"button\">OFF</button></a></p>");
            } else {
              client.println("<p><a href=\"/1/off\"><button class=\"button button2\">ON</button></a></p>");
            }

            // Display current state, and ON/OFF buttons for GPIO 3
            client.println("<p>GPIO 3 - State " + output3State + "</p>");
            // If the output1State is off, it displays the ON button
            if (output3State=="off") {
              client.println("<p><a href=\"/3/on\"><button class=\"button\">OFF</button></a></p>");
            } else {
              client.println("<p><a href=\"/3/off\"><button class=\"button button2\">ON</button></a></p>");
            }

            // Display current state, and ON/OFF buttons for GPIO 4
            client.println("<p>GPIO 4 - State " + output5State + "</p>");
            // If the output5State is off, it displays the ON button
            if (output5State=="off") {
              client.println("<p><a href=\"/4/on\"><button class=\"button\">OFF</button></a></p>");
            } else {
              client.println("<p><a href=\"/4/off\"><button class=\"button button2\">ON</button></a></p>");
            }

            // Display current state, and ON/OFF buttons for GPIO 14
            client.println("<p>GPIO 14 - State " + output5State + "</p>");
            // If the output6State is off, it displays the ON button
            if (output6State=="off") {
              client.println("<p><a href=\"/14/on\"><button class=\"button\">OFF</button></a></p>");
            } else {
              client.println("<p><a href=\"/14/off\"><button class=\"button button2\">ON</button></a></p>");
            }

            // Display current state, and ON/OFF buttons for GPIO 12
            client.println("<p>GPIO 12 - State " + output7State + "</p>");
            // If the output7State is off, it displays the ON button
            if (output7State=="off") {
              client.println("<p><a href=\"/12/on\"><button class=\"button\">OFF</button></a></p>");
            } else {
              client.println("<p><a href=\"/12/off\"><button class=\"button button2\">ON</button></a></p>");
            }

            // Display current state, and ON/OFF buttons for GPIO 13
            client.println("<p>GPIO 13 - State " + output8State + "</p>");
            // If the output8State is off, it displays the ON button
            if (output8State=="off") {
              client.println("<p><a href=\"/13/on\"><button class=\"button\">OFF</button></a></p>");
            } else {
              client.println("<p><a href=\"/13/off\"><button class=\"button button2\">ON</button></a></p>");
            }            

            client.println("</body></html>");

            // The HTTP response ends with another blank line
            client.println();
            // Break out of the while loop
            break;
          } else { // if you got a newline, then clear currentLine
            currentLine = "";
          }
        } else if (c != '\r') {  // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }
      }
    }
    // Clear the header variable
    header = "";
    // Close the connection
    client.stop();
    Serial.println("Client disconnected.");
    Serial.println("");
  }
}
