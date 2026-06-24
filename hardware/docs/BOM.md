# Bill of Materials

Confirmed stack (aerospace / embedded team).

## Active components

| # | Item | Purpose | Notes |
|---|------|---------|-------|
| 1 | **ESP32-S3** dev board | Control, inference, logging | USB-C, 8 MB flash typical; Arduino or PlatformIO |
| 2 | **BMP280** module | Pressure, temperature, altitude | I2C address **0x76** in firmware |
| 3 | **MPU6050** module | Accel + gyro | I2C address **0x68**; shares bus with BMP280 |
| 4 | **Servo motor** | Deploy airbrake | 5–6 V supply; **do not** power from ESP32 3.3 V pin |
| 5 | **2S Li-ion battery** | Primary power | ~7.4 V nominal |
| 6 | **Power switch** | Isolation / safety | Between pack and buck |
| 7 | **XL4015 buck converter** | Step-down | Adjust for **5 V** (servo) and **3.3 V** (MCU + sensors) |

## Supporting items (typical bench build)

- Jumper wires, breadboard or perfboard
- Common ground between ESP32, sensors, servo, and power supply
- USB data cable for flash + serial monitor
- Optional: separate 3.3 V LDO if buck ripple affects baro readings

## Firmware status

| Feature | Status |
|---------|--------|
| BMP280 read | Implemented |
| MPU6050 read | Implemented |
| PINN Cd inference | Implemented (tiny + max profiles) |
| Serial deployment override (`d50`) | Implemented |
| Servo PWM actuation | **Not yet wired** — GPIO reserved in [WIRING.md](WIRING.md) |

## Model profiles

| Profile | Params | Weights | Project |
|---------|--------|---------|---------|
| Tiny | 385 | ~1.5 KB | `hardware/firmware/esp32-airbrake/` |
| Max | 110,593 | ~432 KB | `hardware/firmware/esp32-airbrake-max/` |

Models are trained in `airbrake/` and exported to `include/cd_model*.h` — do not edit headers by hand.
