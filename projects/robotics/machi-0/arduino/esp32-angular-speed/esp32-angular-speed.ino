#include <Wire.h>

#define AS5600_ADDR 0x36
#define ANGLE_HIGH  0x0E
#define ANGLE_LOW   0x0F

// Shared variables
volatile long revCount = 0;
volatile uint16_t rawAngle = 0;
volatile float smoothedDegPerSec = 0;
volatile float totalDegrees = 0;

portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;  // for critical sections

// Sampling parameters
const unsigned long sampleIntervalMicros = 10000UL; // 10 ms = 100 Hz
const float speedAlpha = 0.2;

// Task handles
TaskHandle_t angleTaskHandle = NULL;
TaskHandle_t displayTaskHandle = NULL;

uint16_t readRawAngle() {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(ANGLE_HIGH);
  Wire.endTransmission(false);
Wire.requestFrom(AS5600_ADDR, 2);  // just an int, not uint8_t
  uint8_t high = Wire.read();
  uint8_t low  = Wire.read();
  return ((high & 0x0F) << 8) | low;
}

// ========== FAST TASK: angle + speed computation ==========
void angleTask(void *parameter) {
  uint16_t lastRaw = readRawAngle();
  long lastTotalRaw = (long)revCount * 4096L + lastRaw;
  unsigned long lastMicros = micros();

  for (;;) {
    unsigned long nowMicros = micros();
    if ((nowMicros - lastMicros) >= sampleIntervalMicros) {
      lastMicros += sampleIntervalMicros;

      uint16_t raw = readRawAngle();
      int diff = (int)raw - (int)lastRaw;
      if (diff > 2048) revCount--;
      else if (diff < -2048) revCount++;
      lastRaw = raw;

      long totalRaw = revCount * 4096L + raw;
      long deltaRaw = totalRaw - lastTotalRaw;
      lastTotalRaw = totalRaw;

      float deltaDeg = (float)deltaRaw * 360.0f / 4096.0f;
      float dtSec = (float)sampleIntervalMicros / 1e6f;
      float instDegPerSec = deltaDeg / dtSec;

      portENTER_CRITICAL(&mux);
      smoothedDegPerSec = speedAlpha * instDegPerSec + (1 - speedAlpha) * smoothedDegPerSec;
      rawAngle = raw;
      totalDegrees = (revCount * 360.0f) + (raw * 360.0f / 4096.0f);
      portEXIT_CRITICAL(&mux);
    }
    vTaskDelay(1); // yield to other tasks
  }
}

// ========== SLOW TASK: display ==========
void displayTask(void *parameter) {
  for (;;) {
    vTaskDelay(pdMS_TO_TICKS(500)); // every 500 ms

    portENTER_CRITICAL(&mux);
    float speed = smoothedDegPerSec;
    float rpm = speed / 6.0f;
    float total = totalDegrees;
    portEXIT_CRITICAL(&mux);

    Serial.print("Angle Total: ");
    Serial.print(total, 2);
    Serial.print(" deg   Speed: ");
    Serial.print(speed, 2);
    Serial.print(" deg/s   ");
    Serial.print(rpm, 2);
    Serial.println(" RPM");
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(5,6);
  Wire.setClock(400000);
  delay(1000);

  Serial.println("AS5600 Multi-task Angle & Speed Tracker READY");

  // Create tasks pinned to different cores
  xTaskCreatePinnedToCore(
    angleTask, "AngleTask", 4096, NULL, 2, &angleTaskHandle, 0);

  xTaskCreatePinnedToCore(
    displayTask, "DisplayTask", 4096, NULL, 1, &displayTaskHandle, 1);
}

void loop() {
  // Nothing here — work happens in tasks
}
