# Wiring Guide

## Power (2S + XL4015)

```
2S Li-ion (+) ── switch ── XL4015 IN+
2S Li-ion (-) ───────────── XL4015 IN-  (common GND)

XL4015 OUT (5 V)  ──► Servo +V   (servo stall current: use adequate buck / cap)
XL4015 OUT or LDO ──► ESP32-S3 3.3 V (VIN / 3V3 per board silkscreen)
GND ───────────────► ESP32, BMP280, MPU6050, servo GND (single common ground)
```

**Rules**

- Never feed servo load current through the ESP32 3.3 V regulator.
- Add bulk cap near servo (100–470 µF) if you see brownouts during motion.
- Bench-first: use USB power for ESP32 logic while testing sensors; add battery pack later.

## I2C bus (sensors)

Both sensors share one bus (current firmware):

| Signal | ESP32-S3 GPIO | BMP280 | MPU6050 |
|--------|---------------|--------|---------|
| SDA | **8** | SDA | SDA |
| SCL | **9** | SCL | SCL |
| 3.3 V | 3V3 | VCC | VCC |
| GND | GND | GND | GND |

| Device | I2C address |
|--------|-------------|
| BMP280 | 0x76 |
| MPU6050 | 0x68 |

If BMP280 uses 0x77 on your module, change `bmp.begin(0x76)` in firmware or tie ADDR pin per module datasheet.

## Servo (planned)

| Signal | ESP32-S3 GPIO | Servo |
|--------|---------------|-------|
| PWM signal | **10** (recommended, not in firmware yet) | Signal (orange/yellow) |
| Power | 5 V from buck | +V (red) |
| Ground | GND | GND (brown/black) |

Typical hobby servo pulse: **1000–2000 µs** @ 50 Hz.

Firmware today sets deployment % via serial only (`d0` … `d100`). Servo PWM is the next hardware integration step.

## Serial debug

- **115200 baud**, USB CDC (enable *USB CDC On Boot* in Arduino IDE).
- Commands: `d50`, `help`; max firmware also supports `bench`.

## Pin summary

| GPIO | Function |
|------|----------|
| 8 | I2C SDA |
| 9 | I2C SCL |
| 10 | Servo PWM (reserved) |
