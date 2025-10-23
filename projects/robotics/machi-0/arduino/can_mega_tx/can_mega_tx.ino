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
  while (!Serial); // optional on Mega when connected to USB
  if (CAN.begin(MCP_ANY, CAN_500KBPS, MCP_8MHZ) == CAN_OK)
    Serial.println("CAN init OK!");
  else
    Serial.println("CAN init FAIL!");
  CAN.setMode(MCP_NORMAL);

  Serial.println("Enter angle as decimal (e.g. 180.3) or press Enter to send example.");
}

void sendAngleFloat(float angle) {
  // encode as tenths of degree in big-endian 16-bit
  int16_t raw = (int16_t)round(angle * 10.0f);
  byte data[2];
  data[0] = (raw >> 8) & 0xFF; // high byte
  data[1] = raw & 0xFF;        // low byte

  byte sendStatus = CAN.sendMsgBuf(0x100, 0, 2, data);
  if (sendStatus == CAN_OK) {
    Serial.print("Sent angle: ");
    Serial.print(angle, 1);
    Serial.print(" -> raw: ");
    Serial.println(raw);
  } else {
    Serial.println("Send Error");
  }
}

void loop() {
  // Option A: interactive via Serial
  if (Serial.available()) {
    String s = Serial.readStringUntil('\n');
    s.trim();
    if (s.length() > 0) {
      float angle = s.toFloat();
      sendAngleFloat(angle);
    } else {
      // blank line -> send example
      sendAngleFloat(180.3f);
    }
    delay(200);
    return;
  }

  // Option B: periodic example send (uncomment to use)
  // sendAngleFloat(180.3f); // example: 180.3° -> 1803
  // delay(1000);
}