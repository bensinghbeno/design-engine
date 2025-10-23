/*
MCP2515 pin  MKR WiFi 1010 pin
VCC  3.3V
GND  GND
CS  D7 (you can change if needed)
SO (MISO)  MISO (Pin 10)
SI (MOSI)  MOSI (Pin 8)
SCK  SCK (Pin 9)
INT  D6 (optional but recommended for receive)
CAN_H  to CAN_H from Mega MCP2515
CAN_L  to CAN_L from Mega MCP2515
*/


#include <mcp_can.h>
#include <SPI.h>

const int SPI_CS_PIN = 7;
MCP_CAN CAN(SPI_CS_PIN);

void setup() {
  Serial.begin(115200);
  while (!Serial);
  if (CAN.begin(MCP_ANY, CAN_500KBPS, MCP_8MHZ) == CAN_OK)
    Serial.println("CAN init OK!");
  else
    Serial.println("CAN init FAIL!");
  CAN.setMode(MCP_NORMAL);
}

void loop() {
  if (!digitalRead(6)) { // INT pin goes low when message arrives
    long unsigned int rxId;
    unsigned char len = 0;
    unsigned char rxBuf[8];
    CAN.readMsgBuf(&rxId, &len, rxBuf);
    if (rxId == 0x100) {
      int received = (rxBuf[0] << 8) | rxBuf[1];
      Serial.print("Received: ");
      Serial.println(received);
    }
  }
}
