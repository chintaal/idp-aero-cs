.PHONY: install dev-install lint test generate train-pinn train-baselines benchmark serve clean

PYTHON   := python3
VENV     := .venv
PIP      := $(VENV)/bin/pip
PY       := $(VENV)/bin/python

# ── Environment ──────────────────────────────────────────────────────────────
$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)

install: $(VENV)/bin/activate
	$(PIP) install -e .

dev-install: $(VENV)/bin/activate
	$(PIP) install -e ".[dev]"

# ── Code quality ─────────────────────────────────────────────────────────────
lint:
	$(PY) -m ruff check src/ scripts/ tests/
	$(PY) -m ruff format --check src/ scripts/ tests/

format:
	$(PY) -m ruff format src/ scripts/ tests/

typecheck:
	$(PY) -m mypy src/airbrake --ignore-missing-imports

test:
	$(PY) -m pytest tests/ -v --tb=short

# ── Dataset generation ───────────────────────────────────────────────────────
generate:
	$(PY) scripts/generate_dataset.py \
		--n-flights 3000 \
		--samples 20 \
		--seed 42 \
		--out data/raw/flights.parquet

generate-fast:
	$(PY) scripts/generate_dataset.py \
		--n-flights 500 \
		--samples 10 \
		--seed 42 \
		--out data/raw/flights.parquet

# ── Model training ───────────────────────────────────────────────────────────
train-pinn:
	$(PY) scripts/train_pinn.py \
		--data data/raw/flights.parquet \
		--artifacts artifacts/ \
		--epochs 150 \
		--batch-size 512

train-baselines:
	$(PY) scripts/train_baselines.py \
		--data data/raw/flights.parquet \
		--artifacts artifacts/

benchmark:
	$(PY) scripts/run_benchmark.py \
		--data data/raw/flights.parquet \
		--artifacts artifacts/ \
		--out artifacts/benchmark_results.csv

# ── Full pipeline ─────────────────────────────────────────────────────────────
pipeline: generate train-pinn train-baselines benchmark
	@echo "Pipeline complete. Results in artifacts/"

# ── API ───────────────────────────────────────────────────────────────────────
serve:
	$(PY) -m uvicorn airbrake.api.main:app \
		--host 0.0.0.0 \
		--port 8000 \
		--reload \
		--log-level info

serve-prod:
	$(PY) -m uvicorn airbrake.api.main:app \
		--host 0.0.0.0 \
		--port 8000 \
		--workers 2

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	rm -rf $(VENV) __pycache__ .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete

clean-data:
	rm -rf data/raw/* data/processed/*

clean-artifacts:
	rm -rf artifacts/*
