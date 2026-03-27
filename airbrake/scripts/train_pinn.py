"""
scripts/train_pinn.py
──────────────────────
Train the PINN surrogate ApogeePredictor and save artefacts.

Usage
-----
    python scripts/train_pinn.py
    python scripts/train_pinn.py --data data/raw/flights.parquet --epochs 200
    make train-pinn
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from airbrake.physics.simulation import split_by_flight
from airbrake.training.trainer import train_apogee_predictor

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train PINN apogee predictor")
    parser.add_argument("--data", type=Path, default=Path("data/raw/flights.parquet"))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/"))
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--device", type=str, default=None,
                        help="'cpu' or 'cuda'. Auto-detected if omitted.")
    args = parser.parse_args()

    if not args.data.exists():
        logger.error("Dataset not found: %s — run 'make generate' first.", args.data)
        sys.exit(1)

    import pandas as pd
    df = pd.read_parquet(args.data)
    logger.info("Loaded %d samples from %s", len(df), args.data)

    train_df, val_df, _ = split_by_flight(df, seed=42)
    logger.info("Train: %d  Val: %d", len(train_df), len(val_df))

    model = train_apogee_predictor(
        train_df=train_df,
        val_df=val_df,
        artifacts_dir=args.artifacts,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        patience=args.patience,
        device=args.device,
    )

    # Quick sanity check: print parameter count
    n_params = sum(p.numel() for p in model.parameters())
    logger.info("Model parameters: {:,}".format(n_params))
    logger.info("Artefacts saved to:  %s", args.artifacts)


if __name__ == "__main__":
    main()
