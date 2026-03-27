"""
scripts/run_benchmark.py
─────────────────────────
Evaluate all trained models on the held-out test split and print a ranked table.

Usage
-----
    python scripts/run_benchmark.py
    make benchmark
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from airbrake.physics.simulation import split_by_flight
from airbrake.training.benchmark import benchmark_all

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark all trained models")
    parser.add_argument("--data", type=Path, default=Path("data/raw/flights.parquet"))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/benchmark_results.csv"))
    args = parser.parse_args()

    if not args.data.exists():
        logger.error("Dataset not found: %s — run 'make generate' first.", args.data)
        sys.exit(1)

    import pandas as pd
    df = pd.read_parquet(args.data)
    _, _, test_df = split_by_flight(df, seed=42)
    logger.info("Test set: %d samples from %d unique flights",
                len(test_df), test_df["flight_id"].nunique())

    results_df = benchmark_all(test_df, artifacts_dir=args.artifacts, output_csv=args.out)

    print("\n" + "=" * 70)
    print("  BENCHMARK RESULTS (test set, sorted by MAE)")
    print("=" * 70)
    print(results_df.to_string(index=False))
    print("=" * 70)

    best = results_df.iloc[0]
    logger.info("Best model: %s  MAE=%.1f m  RMSE=%.1f m  R²=%.4f",
                best["model"], best["mae_m"], best["rmse_m"], best["r2"])


if __name__ == "__main__":
    main()
