# ESP32-S3 Airbrake Firmware

TinyML drag-coefficient PINN running on ESP32-S3 with BMP280 + MPU6050.

## Quick start

```bash
# Tiny profile (385 params, ~1.5 KB)
make train-cd
make firmware

# Max profile (110K params, ~432 KB) — see ../esp32-airbrake-max/
make train-cd-max
make firmware-max
```

## Project layout

```
firmware/esp32-airbrake/
├── platformio.ini      # ESP32-S3 board + Adafruit libs
├── include/cd_model.h  # auto-generated PINN weights (~1.5 KB)
└── src/main.cpp        # sensors + inference loop
```

## Serial commands

| Command | Action |
|---------|--------|
| `d50`   | Set airbrake deployment to 50 % |
| `help`  | List commands |

## Hardware

| Device   | I2C address | Pins (SDA/SCL) |
|----------|-------------|----------------|
| BMP280   | 0x76        | GPIO 8 / 9     |
| MPU6050  | 0x68        | GPIO 8 / 9     |

## Retrain after new CFD data

Update `real-data-new.txt` at repo root, then:

```bash
make train-cd
make firmware
```

This regenerates `include/cd_model.h` and the root-level `cd_model.h` copy.
