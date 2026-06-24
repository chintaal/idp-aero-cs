# Hardware (side track)

Bench / flight electronics for the airbrake demo — **separate from the main ML pipeline** in `airbrake/`.

This folder is a **byproduct consumer**: training happens in Python; exported model headers are flashed here.

## Bill of materials (confirmed)

| Part | Role |
|------|------|
| ESP32-S3 | MCU, PINN inference, PWM, serial |
| BMP280 | Barometric pressure / altitude |
| MPU6050 | Accelerometer + gyroscope |
| Servo motor | Airbrake deployment (PWM — planned) |
| 2S Li-ion + switch + XL4015 buck | Power rail |

See [docs/BOM.md](docs/BOM.md) and [docs/WIRING.md](docs/WIRING.md).

## Layout

```
hardware/
├── docs/                  BOM, wiring, Arduino IDE handoff
├── firmware/              PlatformIO projects (tiny + max PINN)
│   ├── esp32-airbrake/
│   └── esp32-airbrake-max/
└── arduino/               Zip-and-send sketches for Arduino IDE
    ├── esp32_airbrake/
    └── esp32_airbrake_max/
```

## Pipeline separation

```
real-data-new.txt  →  airbrake/ (expand + train PINN)  →  cd_model*.h
                                                              ↓
                                                         hardware/ (flash)
```

| Step | Where | Command |
|------|-------|---------|
| Train + export | `airbrake/` | `make train-cd` or `make train-cd-max` |
| Sync Arduino sketches | repo root | `make sync-hardware` |
| Compile (no flash) | `hardware/firmware/` | `make firmware` |
| Flash | `hardware/firmware/` | `make firmware-upload` |

## Quick start (PlatformIO)

```bash
make train-cd          # from repo root — exports headers + syncs arduino/
make firmware          # compile tiny profile
make firmware-upload   # flash ESP32-S3
make firmware-monitor  # serial @ 115200
```

## Arduino IDE (teammate)

See [docs/ARDUINO-IDE-HANDOFF.md](docs/ARDUINO-IDE-HANDOFF.md). Zip `hardware/arduino/esp32_airbrake/` and upload — no PlatformIO or Python required.

## Main project docs

High-level embedded architecture remains in `docs/05_Architecture/Embedded-Electronics-and-Sensing.md`. Pin maps, BOM, and flash steps live **here** in `hardware/docs/`.
