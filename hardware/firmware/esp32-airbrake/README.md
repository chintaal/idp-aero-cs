# ESP32-S3 Airbrake Firmware (Tiny PINN)

Minimal drag-coefficient PINN for first hardware bring-up.

Parent folder: [../../README.md](../../README.md)

## Quick start

```bash
# From repo root
make train-cd          # train + export cd_model.h + sync arduino/
make firmware          # compile only
make firmware-upload   # flash
make firmware-monitor  # serial @ 115200
```

## Layout

```
hardware/firmware/esp32-airbrake/
├── platformio.ini
├── include/cd_model.h   # auto-generated (~385 params)
└── src/main.cpp
```

## Arduino IDE

See [../../docs/ARDUINO-IDE-HANDOFF.md](../../docs/ARDUINO-IDE-HANDOFF.md) — use `hardware/arduino/esp32_airbrake/`.

## Hardware

BMP280 + MPU6050 on I2C GPIO 8/9. See [../../docs/WIRING.md](../../docs/WIRING.md).
