#!/usr/bin/env python3
"""Copy PlatformIO sources + model headers into Arduino IDE sketch folders."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HW = ROOT / "hardware"


def sync_sketch(name: str, src_main: Path, src_header: Path, ino_name: str, header_name: str) -> None:
    dest = HW / "arduino" / name
    dest.mkdir(parents=True, exist_ok=True)

    text = src_main.read_text(encoding="utf-8")
    text = text.replace(
        "PlatformIO project: firmware/esp32-airbrake/",
        f"Arduino IDE sketch — see hardware/arduino/{name}/",
    )
    text = text.replace(
        "PlatformIO project: firmware/esp32-airbrake-max/",
        f"Arduino IDE sketch — see hardware/arduino/{name}/",
    )
    (dest / ino_name).write_text(text, encoding="utf-8")
    shutil.copy2(src_header, dest / header_name)
    print(f"Synced {dest}/")


def main() -> None:
    sync_sketch(
        "esp32_airbrake",
        HW / "firmware/esp32-airbrake/src/main.cpp",
        HW / "firmware/esp32-airbrake/include/cd_model.h",
        "esp32_airbrake.ino",
        "cd_model.h",
    )
    sync_sketch(
        "esp32_airbrake_max",
        HW / "firmware/esp32-airbrake-max/src/main.cpp",
        HW / "firmware/esp32-airbrake-max/include/cd_model_max.h",
        "esp32_airbrake_max.ino",
        "cd_model_max.h",
    )


if __name__ == "__main__":
    main()
