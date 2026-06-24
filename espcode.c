/**
 * Legacy pointer — hardware lives under hardware/
 *
 *   hardware/firmware/esp32-airbrake/       PlatformIO (tiny PINN)
 *   hardware/firmware/esp32-airbrake-max/   PlatformIO (max PINN)
 *   hardware/arduino/                       Arduino IDE handoff
 *
 * From repo root:
 *   make train-cd          train + export + sync arduino sketches
 *   make firmware          compile (no flash)
 *   make firmware-upload   flash ESP32-S3
 */
