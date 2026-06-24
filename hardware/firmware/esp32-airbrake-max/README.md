# ESP32-S3 MAX PINN Firmware

Largest Cd PINN under ESP32-S3 flash/stack budgets (~110K params, ~432 KB fp32).

Parent folder: [../../README.md](../../README.md)

## Size envelope

| Resource | This model |
|----------|------------|
| Parameters | 110,593 |
| Weights (PROGMEM) | ~432 KB |
| Stack scratch | 2,048 B |
| Architecture | `[256, 256, 128, 64, 32]` |

Compare with tiny profile in `../esp32-airbrake/` (385 params, 1.5 KB).

## Commands

```bash
make train-cd-max
make firmware-max
make firmware-max-upload
make firmware-max-monitor
```

Serial: `d50`, `bench`, `help` @ 115200.

## Arduino IDE

See [../../docs/ARDUINO-IDE-HANDOFF.md](../../docs/ARDUINO-IDE-HANDOFF.md) — use `hardware/arduino/esp32_airbrake_max/`.

## Files

```
hardware/firmware/esp32-airbrake-max/
├── platformio.ini
├── max_app.csv              # optional 2 MB app partition
├── include/cd_model_max.h   # generated
└── src/main.cpp
```

Training artefacts: `airbrake/artifacts/cd_pinn_max/`
