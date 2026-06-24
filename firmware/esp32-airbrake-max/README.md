# ESP32-S3 MAX PINN Firmware

Largest physics-informed Cd network that still fits **ESP32-S3 without PSRAM**.

## Size envelope

| Resource | Budget | This model |
|----------|--------|------------|
| Weights (flash / PROGMEM) | ≤ 450 KB fp32 | **~432 KB** |
| Inference stack scratch | ≤ 8 KB | **2,048 B** |
| Parameters | — | **110,593** |
| Architecture | — | `[256, 256, 128, 64, 32]` |

Compare with the minimal firmware in `../esp32-airbrake/`:

| Profile | Params | Weights | Directory |
|---------|--------|---------|-----------|
| Tiny | 385 | 1.5 KB | `esp32-airbrake/` |
| **Max** | **110,593** | **432 KB** | **`esp32-airbrake-max/`** |

Weights are stored in **PROGMEM** (flash), not SRAM. Inference uses two ping-pong activation buffers sized to the widest layer (256 neurons).

## Commands

```bash
# Train max model + export header
make train-cd-max

# Build / flash / monitor
make firmware-max
make firmware-max-upload
make firmware-max-monitor
```

Inside `airbrake/`:

```bash
python scripts/esp32_sizing.py          # show ESP32 budget search
python scripts/train_pinn_cd_max.py     # train + export
```

## Serial (115200)

| Command | Action |
|---------|--------|
| `d50` | Set deployment to 50 % |
| `bench` | Run 1000× inference timing |
| `help` | List commands |

## Pushing further

If you quantize to INT8 (~108 KB weights), you can grow width on the same flash budget. The `esp32-s3-max-app` environment uses a 2 MB app partition (`max_app.csv`) for experiments beyond 450 KB fp32.

## Files

```
esp32-airbrake-max/
├── platformio.ini
├── max_app.csv              # optional 2 MB app partition
├── include/cd_model_max.h   # generated — do not edit
└── src/main.cpp
```

Training artefacts: `airbrake/artifacts/cd_pinn_max/`
