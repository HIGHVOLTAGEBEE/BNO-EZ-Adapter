#include <Wire.h>
#include <Adafruit_BNO08x.h>
#include <Adafruit_NeoPixel.h>

#define SDA_BNO 8
#define SCL_BNO 9

#define SDA_SLAVE 10
#define SCL_SLAVE 11

#define INT_PIN   7
#define RESET_PIN 4

#define NEOPIXEL_PIN 48
#define SLAVE_ADDR 0x22

Adafruit_BNO08x bno08x;
sh2_SensorValue_t sensorValue;
Adafruit_NeoPixel pixel(1, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

enum SystemStatus {
  STATE_OK,
  STATE_BNO_ERROR,
  STATE_I2C_SLAVE_ERROR
};

volatile SystemStatus status = STATE_OK;
volatile bool dataReady = false;
volatile float headingRaw = 0;
volatile float zeroOffset = 0;
volatile int headingInt = 0;

String serialInput = "";

void IRAM_ATTR onDataReady() {
  dataReady = true;
}

float getHeading(sh2_SensorValue_t *sv) {
  float qr = sv->un.rotationVector.real;
  float qi = sv->un.rotationVector.i;
  float qj = sv->un.rotationVector.j;
  float qk = sv->un.rotationVector.k;

  float yaw = atan2(2.0 * (qr * qk + qi * qj),
                    1.0 - 2.0 * (qj * qj + qk * qk));

  yaw = yaw * 180.0 / PI;
  if (yaw < 0) yaw += 360.0;

  return yaw;
}

void handleSerial() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {

      if (serialInput == "0") {
        zeroOffset = headingRaw;
        Serial.println("✔ Zero gesetzt (Serial)");
      }

      else if (serialInput == "r") {
        zeroOffset = headingRaw;
        Serial.println("✔ Reset Zero");
      }

      else if (serialInput == "s") {
        Serial.print("Heading=");
        Serial.print(headingInt);
        Serial.print(" Raw=");
        Serial.print(headingRaw);
        Serial.print(" Zero=");
        Serial.print(zeroOffset);
        Serial.print(" Status=");
        Serial.println(status);
      }

      serialInput = "";
    } else {
      serialInput += c;
    }
  }
}

void onReceive(int len) {
  while (Wire1.available()) {
    uint8_t cmd = Wire1.read();

    if (cmd == 0x10) {
      zeroOffset = headingRaw;
      Serial.println("✔ Zero via I2C gesetzt");
    }
  }
}

void onRequest() {
  int value = headingInt;
  Wire1.write((value >> 8) & 0xFF);
  Wire1.write(value & 0xFF);
}

void setLED(uint8_t r, uint8_t g, uint8_t b, uint8_t br) {
  pixel.setBrightness(br);
  pixel.setPixelColor(0, pixel.Color(r, g, b));
  pixel.show();
}

uint8_t breathing() {
  float t = (millis() % 5000) / 5000.0;
  return 30 + (sin(t * 2 * PI) + 1) * 45;
}

void setup() {
  Serial.begin(1000000);
  delay(1000);

  pixel.begin();

  pinMode(RESET_PIN, OUTPUT);
  pinMode(INT_PIN, INPUT);

  digitalWrite(RESET_PIN, LOW);
  delay(50);
  digitalWrite(RESET_PIN, HIGH);
  delay(300);

  Wire.begin(SDA_BNO, SCL_BNO, 400000);

  if (!bno08x.begin_I2C()) {
    status = STATE_BNO_ERROR;
    Serial.println("BNO085 FAIL");
  }

  attachInterrupt(digitalPinToInterrupt(INT_PIN), onDataReady, FALLING);

  bno08x.enableReport(SH2_ROTATION_VECTOR, 1250);

  Wire1.begin(SLAVE_ADDR, SDA_SLAVE, SCL_SLAVE, 400000);
  Wire1.onReceive(onReceive);
  Wire1.onRequest(onRequest);

  Serial.println("SYSTEM READY");
}

void loop() {

  handleSerial();

  if (dataReady) {
    dataReady = false;

    while (bno08x.getSensorEvent(&sensorValue)) {

      if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {

        headingRaw = getHeading(&sensorValue);

        float corrected = headingRaw - zeroOffset;

        if (corrected < 0) corrected += 360;
        if (corrected >= 360) corrected -= 360;

        headingInt = (int)corrected;

        status = STATE_OK;
      }
    }
  }

  uint8_t br = breathing();

  if (status == STATE_OK) setLED(0,255,0,br);
  else if (status == STATE_BNO_ERROR) setLED(255,0,0,br);
  else setLED(255,80,0,br);

  static uint32_t t = 0;
  if (millis() - t > 100) {
    t = millis();

    Serial.print("H:");
    Serial.print(headingInt);

    Serial.print(" R:");
    Serial.print(headingRaw);

    Serial.print(" Z:");
    Serial.print(zeroOffset);

    Serial.print(" S:");
    Serial.println(status);
  }
}