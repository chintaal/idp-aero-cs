"""
scripts/train_baselines.py
───────────────────────────
Fit all sklearn / GBDT baseline models and serialise them to artifacts/.

Usage
-----
    python scripts/train_baselines.py
    make train-baselines
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from airbrake.models.baselines import ALL_BASELINES, FEATURE_COLS, TARGET_COL, save_model
from airbrake.physics.simulation import split_by_flight

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train all baseline models")
    parser.add_argument("--data", type=Path, default=Path("data/raw/flights.parquet"))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/"))
    parser.add_argument("--models", nargs="+", default=list(ALL_BASELINES.keys()),
                        help="Subset of models to train")
    args = parser.parse_args()

    if not args.data.exists():
        logger.error("Dataset not found: %s — run 'make generate' first.", args.data)
        sys.exit(1)

    import numpy as np
    import pandas as pd
    from sklearn.metrics import mean_absolute_error

    df = pd.read_parquet(args.data)
    train_df, val_df, _ = split_by_flight(df, seed=42)

    X_train = train_df[FEATURE_COLS].values
    y_train = train_df[TARGET_COL].values
    X_val = val_df[FEATURE_COLS].values
    y_val = val_df[TARGET_COL].values

    logger.info("Training %d baselines on %d samples …", len(args.models), len(X_train))

    results: list[dict] = []
    for name in args.models:
        if name not in ALL_BASELINES:
            logger.warning("Unknown baseline '%s' — skipping.", name)
            continue

        builder = ALL_BASELINES[name]
        model = builder()

        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        train_time = time.perf_counter() - t0

        pred_val = model.predict(X_val)
        mae = mean_absolute_error(y_val, pred_val)

        save_model(model, args.artifacts / f"{name}_model.pkl")
        results.append({"model": name, "train_time_s": round(train_time, 2), "val_mae_m": round(mae, 3)})
        logger.info("  %-20s  val MAE = %.1f m  (%.1f s)", name, mae, train_time)

    import pandas as pd
    summary = pd.DataFrame(results).sort_values("val_mae_m")
    print("\n" + summary.to_string(index=False))

    out_csv = args.artifacts / "baseline_val_results.csv"
    summary.to_csv(out_csv, index=False)
    logger.info("Summary → %s", out_csv)


if __name__ == "__main__":
    main()
