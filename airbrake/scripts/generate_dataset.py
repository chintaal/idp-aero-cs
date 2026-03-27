"""
scripts/generate_dataset.py
────────────────────────────
Generate the Monte Carlo training dataset and save as Parquet.

Usage
-----
    python scripts/generate_dataset.py                    # defaults
    python scripts/generate_dataset.py --n-flights 5000 --seed 7

    # via Makefile
    make generate
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# Allow running from project root without 'pip install -e .'
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from airbrake.physics.simulation import generate_dataset, split_by_flight

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate airbrake simulation dataset")
    parser.add_argument("--n-flights", type=int, default=3_000,
                        help="Number of Monte Carlo flights to simulate")
    parser.add_argument("--samples", type=int, default=20,
                        help="State snapshots per flight (coast phase)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("data/raw/flights.parquet"),
                        help="Output path for the raw dataset")
    parser.add_argument("--split", action="store_true",
                        help="Also write train/val/test parquet splits")
    args = parser.parse_args()

    t0 = time.perf_counter()
    logger.info("Simulating %d flights …", args.n_flights)

    df = generate_dataset(
        n_flights=args.n_flights,
        samples_per_flight=args.samples,
        seed=args.seed,
    )

    # Save to parquet
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    elapsed = time.perf_counter() - t0
    logger.info("Saved %d rows → %s  (%.1f s)", len(df), args.out, elapsed)

    # Descriptive stats
    print(df[["h", "v", "target_apogee"]].describe().round(2).to_string())

    if args.split:
        train_df, val_df, test_df = split_by_flight(df, seed=args.seed)
        base = args.out.parent
        for name, split in [("train", train_df), ("val", val_df), ("test", test_df)]:
            path = base / f"{name}.parquet"
            split.to_parquet(path, index=False)
            logger.info("  %s: %d rows → %s", name, len(split), path)


if __name__ == "__main__":
    main()
