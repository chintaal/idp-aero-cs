.PHONY: train-cd expand-cd train-cd-max sync-hardware firmware firmware-upload firmware-monitor \
        firmware-max firmware-max-upload firmware-max-monitor clean-firmware clean-firmware-max \
        esp32-sizing

AIRBRAKE_DIR := airbrake
HARDWARE_DIR := hardware
FIRMWARE_DIR := $(HARDWARE_DIR)/firmware/esp32-airbrake
FIRMWARE_MAX_DIR := $(HARDWARE_DIR)/firmware/esp32-airbrake-max
VENV := $(AIRBRAKE_DIR)/.venv/bin/activate

train-cd: expand-cd
	. $(VENV) && cd $(AIRBRAKE_DIR) && python scripts/train_pinn_cd.py
	$(MAKE) sync-hardware

train-cd-max: expand-cd
	. $(VENV) && cd $(AIRBRAKE_DIR) && python scripts/train_pinn_cd_max.py
	$(MAKE) sync-hardware

expand-cd:
	. $(VENV) && cd $(AIRBRAKE_DIR) && python scripts/expand_real_data.py

sync-hardware:
	. $(VENV) && cd $(AIRBRAKE_DIR) && python scripts/sync_hardware.py

esp32-sizing:
	. $(VENV) && cd $(AIRBRAKE_DIR) && python scripts/esp32_sizing.py

firmware:
	cd $(FIRMWARE_DIR) && pio run

firmware-upload:
	cd $(FIRMWARE_DIR) && pio run -t upload

firmware-monitor:
	cd $(FIRMWARE_DIR) && pio device monitor

firmware-max:
	cd $(FIRMWARE_MAX_DIR) && pio run

firmware-max-upload:
	cd $(FIRMWARE_MAX_DIR) && pio run -t upload

firmware-max-monitor:
	cd $(FIRMWARE_MAX_DIR) && pio device monitor

clean-firmware:
	cd $(FIRMWARE_DIR) && pio run -t clean

clean-firmware-max:
	cd $(FIRMWARE_MAX_DIR) && pio run -t clean
