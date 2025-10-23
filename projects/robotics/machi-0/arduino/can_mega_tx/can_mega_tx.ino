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
  int value = 707;
  byte data[2];
  data[0] = (value >> 8) & 0xFF;
  data[1] = value & 0xFF;

  byte sendStatus = CAN.sendMsgBuf(0x100, 0, 2, data);
  if (sendStatus == CAN_OK)
    Serial.println("Message Sent: 777");
  else
    Serial.println("Send Error");

  delay(1000);
}
