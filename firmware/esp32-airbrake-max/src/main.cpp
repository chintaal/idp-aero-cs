/**
 * ESP32-S3 MAX PINN firmware — largest Cd PINN under flash/stack budgets.
 *
 * Project: firmware/esp32-airbrake-max/
 * Model:   include/cd_model_max.h  (~110K params, ~432 KB fp32 PROGMEM)
 *
 * Serial commands:
 *   d50    set deployment %
 *   bench  run 1000 inference timing samples
 *   help
 */

#include <Arduino.h>
#include <Wire.h>
#include <math.h>

#include <Adafruit_BMP280.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

#include "cd_model_max.h"

namespace {

constexpr float kSeaLevelHpa = 1013.25f;
constexpr float kSpeedOfSound = 343.0f;
constexpr float kRAir = 287.058f;
constexpr float kLoopDtS = 0.05f;
constexpr int kI2cSda = 8;
constexpr int kI2cScl = 9;

Adafruit_BMP280 bmp;
Adafruit_MPU6050 mpu;

float g_deployment_pct = 0.0f;
float g_prev_alt_m = 0.0f;
float g_velocity_m_s = 0.0f;
bool g_have_prev_alt = false;
unsigned long g_last_loop_ms = 0;

constexpr float kAreaDeployPct[] = {
    0.0f, 12.5f, 25.0f, 37.5f, 50.0f, 62.5f, 75.0f, 87.5f, 100.0f,
};
constexpr float kAreaM2[] = {
    0.013993f, 0.015501f, 0.016506f, 0.017361f, 0.01805f,
    0.018697f, 0.01927f, 0.019775f, 0.020235f,
};
constexpr int kAreaNAnchors = sizeof(kAreaDeployPct) / sizeof(kAreaDeployPct[0]);

float lerp(float a, float b, float t) { return a + (b - a) * t; }

float areaFromDeployment(float deploy_pct) {
  if (deploy_pct <= kAreaDeployPct[0]) return kAreaM2[0];
  if (deploy_pct >= kAreaDeployPct[kAreaNAnchors - 1]) return kAreaM2[kAreaNAnchors - 1];
  for (int i = 0; i < kAreaNAnchors - 1; i++) {
    if (deploy_pct >= kAreaDeployPct[i] && deploy_pct <= kAreaDeployPct[i + 1]) {
      const float t = (deploy_pct - kAreaDeployPct[i]) /
                      (kAreaDeployPct[i + 1] - kAreaDeployPct[i]);
      return lerp(kAreaM2[i], kAreaM2[i + 1], t);
    }
  }
  return kAreaM2[0];
}

float densityFromBaro(float pressure_pa, float temp_c) {
  float temp_k = temp_c + 273.15f;
  if (temp_k < 200.0f) temp_k = 288.15f;
  return pressure_pa / (kRAir * temp_k);
}

float estimateVelocity(float alt_m, float accel_z_m_s2, float dt_s) {
  float v_baro = 0.0f;
  if (g_have_prev_alt && dt_s > 1e-4f) {
    v_baro = (alt_m - g_prev_alt_m) / dt_s;
  }
  g_prev_alt_m = alt_m;
  g_have_prev_alt = true;

  constexpr float alpha = 0.85f;
  g_velocity_m_s = alpha * (g_velocity_m_s + accel_z_m_s2 * dt_s) + (1.0f - alpha) * v_baro;
  return fabsf(g_velocity_m_s);
}

float runMaxInference(
    float deploy_pct,
    float velocity_m_s,
    float density_kg_m3,
    float area_m2,
    float* out_drag_n) {
  float mach = velocity_m_s / kSpeedOfSound;
  if (mach < 0.05f) mach = 0.05f;

  const float features[CD_MAX_N_FEATURES] = {
      deploy_pct,
      mach,
      velocity_m_s,
      density_kg_m3,
      area_m2,
  };

  const float cd = cd_max_predict(features);
  const float drag = cd_max_drag_force(cd, density_kg_m3, velocity_m_s, area_m2);
  if (out_drag_n) *out_drag_n = drag;
  return cd;
}

void benchmarkInference() {
  const float features[CD_MAX_N_FEATURES] = {50.0f, 0.2f, 68.6f, 1.17f, 0.018f};
  const int samples = 1000;

  cd_max_predict(features);

  const uint32_t t0 = micros();
  volatile float sink = 0.0f;
  for (int i = 0; i < samples; i++) {
    sink += cd_max_predict(features);
  }
  const uint32_t elapsed = micros() - t0;
  (void)sink;

  Serial.println("--- MAX PINN benchmark ---");
  Serial.printf("Samples:     %d\n", samples);
  Serial.printf("Total:       %lu us\n", (unsigned long)elapsed);
  Serial.printf("Per infer:   %.1f us\n", elapsed / (float)samples);
  Serial.printf("Params:      %d\n", CD_MAX_N_PARAMS);
  Serial.printf("Weights:     %.1f KB fp32 (PROGMEM)\n", CD_MAX_WEIGHT_KB);
  Serial.printf("Stack scratch: %d B\n", CD_MAX_STACK_BYTES);
  Serial.println("---");
}

void handleSerialCommands() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd.startsWith("d")) {
    const float pct = cmd.substring(1).toFloat();
    if (pct >= 0.0f && pct <= 100.0f) {
      g_deployment_pct = pct;
      Serial.printf("Deployment set to %.1f %%\n", g_deployment_pct);
    } else {
      Serial.println("Usage: d0 .. d100");
    }
  } else if (cmd == "bench" || cmd == "b") {
    benchmarkInference();
  } else if (cmd == "help" || cmd == "?") {
    Serial.println("Commands:");
    Serial.println("  d<N>    set deployment percent (0-100)");
    Serial.println("  bench   run inference timing benchmark");
    Serial.println("  help    show this message");
  }
}

void printInferenceBlock(
    float temp_c,
    float pressure_pa,
    float alt_m,
    float accel_z,
    float gyro_z) {
  const unsigned long now_ms = millis();
  const float dt_s = (g_last_loop_ms == 0)
                         ? kLoopDtS
                         : (now_ms - g_last_loop_ms) / 1000.0f;
  g_last_loop_ms = now_ms;

  const float density = densityFromBaro(pressure_pa, temp_c);
  const float velocity = estimateVelocity(alt_m, accel_z, dt_s);
  const float area = areaFromDeployment(g_deployment_pct);
  const float mach = velocity / kSpeedOfSound;

  const uint32_t t0 = micros();
  float drag_n = 0.0f;
  const float cd = runMaxInference(g_deployment_pct, velocity, density, area, &drag_n);
  const uint32_t infer_us = micros() - t0;

  Serial.println("--- MAX PINN inference ---");
  Serial.printf("Deploy:   %.1f %%  |  Area: %.6f m2\n", g_deployment_pct, area);
  Serial.printf("Alt:      %.1f m  |  V: %.2f m/s  |  Mach: %.3f\n", alt_m, velocity, mach);
  Serial.printf("Rho:      %.4f kg/m3  |  P: %.0f Pa  |  T: %.1f C\n",
                density, pressure_pa, temp_c);
  Serial.printf("Cd pred:  %.4f  |  Drag: %.3f N  |  infer: %lu us\n",
                cd, drag_n, (unsigned long)infer_us);
  Serial.printf("Model:    %d params  |  %.1f KB fp32  |  stack %d B\n",
                CD_MAX_N_PARAMS, CD_MAX_WEIGHT_KB, CD_MAX_STACK_BYTES);
  Serial.printf("IMU Z:    accel %.2f m/s2  |  gyro %.2f rad/s\n", accel_z, gyro_z);
  Serial.println("---");
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(2000);

  Wire.begin(kI2cSda, kI2cScl);

  if (!bmp.begin(0x76)) {
    Serial.println("BMP280 FAILED — check wiring / I2C address 0x76");
    while (true) delay(100);
  }
  Serial.println("BMP280 OK");

  if (!mpu.begin(0x68)) {
    Serial.println("MPU6050 FAILED — check wiring / I2C address 0x68");
    while (true) delay(100);
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  Serial.println("MPU6050 OK");

  Serial.println("MAX Cd PINN loaded (ESP32-S3). Type 'help' for commands.");
  Serial.printf("Profile: %d params, %.1f KB weights, %d B stack\n",
                CD_MAX_N_PARAMS, CD_MAX_WEIGHT_KB, CD_MAX_STACK_BYTES);
  Serial.println("---");
}

void loop() {
  handleSerialCommands();

  const float temp_c = bmp.readTemperature();
  const float pressure_pa = bmp.readPressure();
  const float alt_m = bmp.readAltitude(kSeaLevelHpa);

  sensors_event_t accel;
  sensors_event_t gyro;
  sensors_event_t temp;
  mpu.getEvent(&accel, &gyro, &temp);

  printInferenceBlock(temp_c, pressure_pa, alt_m, accel.acceleration.z, gyro.gyro.z);

  delay(static_cast<int>(kLoopDtS * 1000.0f));
}
