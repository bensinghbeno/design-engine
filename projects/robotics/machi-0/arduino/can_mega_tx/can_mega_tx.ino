/*
MCP2515 pin	Arduino Mega pin
VCC	        5 V
GND		      GND
CS			    47
SO 			    (MISO)	50
SI 			    (MOSI)	51
SCK				  52
INT				  not connected (optional)
CAN H / CAN L	to CAN bus twisted pair (with 120 Ω termination at one end)
*/
#include <mcp_can.h>
#include <SPI.h>

const int SPI_CS_PIN = 47;
const int CAN_INT_PIN = 2; // <- connect MCP2515 INT pin here
MCP_CAN CAN(SPI_CS_PIN);

void setup() {
  Serial.begin(115200);
  while (!Serial);
  pinMode(CAN_INT_PIN, INPUT_PULLUP);

  if (CAN.begin(MCP_ANY, CAN_500KBPS, MCP_8MHZ) == CAN_OK)
    Serial.println("CAN init OK!");
  else
    Serial.println("CAN init FAIL!");
  CAN.setMode(MCP_NORMAL);

  Serial.println("Enter angle as decimal (e.g. 180.3) or press Enter to send example.");
}

void sendAngleFloat(float angle) {
  int16_t raw = (int16_t)round(angle * 10.0f);
  byte data[2];
  data[0] = (raw >> 8) & 0xFF;
  data[1] = raw & 0xFF;
  CAN.sendMsgBuf(0x100, 0, 2, data);
}

void checkForStatus() {
  if (!digitalRead(CAN_INT_PIN)) { // message waiting
    unsigned long rxId;
    unsigned char len = 0;
    unsigned char rxBuf[8];
    if (CAN.readMsgBuf(&rxId, &len, rxBuf) == CAN_OK) {
      if (rxId == 0x101 && len >= 4) {
        uint16_t rawTenths = ((uint16_t)rxBuf[0] << 8) | rxBuf[1];
        uint16_t contTenths = ((uint16_t)rxBuf[2] << 8) | rxBuf[3];
        float rawDeg = rawTenths / 10.0f;
        float contDeg = contTenths / 10.0f;
        Serial.print("Remote Raw: ");
        Serial.println(rawDeg, 2);
        Serial.print("Remote Continuous: ");
        Serial.println(contDeg, 2);
        if (len >= 5) {
          Serial.print("OnTarget: ");
          Serial.println(rxBuf[4] ? "YES" : "NO");
        }
      } else {
        Serial.print("Got CAN id ");
        Serial.print(rxId, HEX);
        Serial.print(" len ");
        Serial.println(len);
      }
    }
  }
}

void loop() {
  // unchanged: serial -> sendAngleFloat(...) when you type angle
  if (Serial.available()) {
    String s = Serial.readStringUntil('\n');
    s.trim();
    if (s.length() > 0) {
      float angle = s.toFloat();
      sendAngleFloat(angle);
    } else {
      sendAngleFloat(180.3f);
    }
    delay(200);
  }

  // regularly poll for remote status frames
  checkForStatus();

  // small delay to avoid busy-loop
  delay(10);
}