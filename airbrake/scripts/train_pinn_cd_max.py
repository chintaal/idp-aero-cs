"""
Train the largest Cd PINN that still fits ESP32-S3 flash + stack budgets.

Default architecture is chosen by esp32_sizing.py under:
  - <= 450 KB fp32 weights (PROGMEM / flash)
  - <= 8 KB inference scratch (two activation buffers)

Exports to firmware/esp32-airbrake-max/include/cd_model_max.h

Usage:
    python scripts/expand_real_data.py
    python scripts/train_pinn_cd_max.py
    python scripts/esp32_sizing.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from esp32_model_export import export_c_header  # noqa: E402
from esp32_sizing import search_max_arch  # noqa: E402
from train_pinn_cd import (  # noqa: E402
    FEATURE_COLS,
    TARGET_COL,
    MinMaxScaler,
    TinyCdPINN,
    monotonic_loss,
    physics_loss,
    train,
)

DEFAULT_EXPORT = Path("../firmware/esp32-airbrake-max/include/cd_model_max.h")
DEFAULT_ARTIFACTS = Path("artifacts/cd_pinn_max")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train max-size Cd PINN for ESP32-S3")
    parser.add_argument("--data", type=Path, default=Path("data/processed/cd_expanded.csv"))
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--export-header", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--epochs", type=int, default=2500)
    parser.add_argument("--lr", type=float, default=8e-4)
    parser.add_argument("--max-weight-kb", type=float, default=450.0)
    parser.add_argument("--max-stack-bytes", type=int, default=8192)
    parser.add_argument(
        "--hidden",
        type=int,
        nargs="+",
        default=None,
        help="Override auto-selected hidden dims",
    )
    args = parser.parse_args()

    if not args.data.exists():
        print(f"Dataset missing: {args.data} — run expand_real_data.py first")
        sys.exit(1)

    if args.hidden:
        hidden = tuple(args.hidden)
        n_params = sum(
            a * b + b
            for a, b in zip(
                [len(FEATURE_COLS), *hidden],
                [*hidden, 1],
            )
        )
        sizing = {
            "hidden": list(hidden),
            "n_params": n_params,
            "weight_kb": round(n_params * 4 / 1024.0, 2),
            "stack_bytes": 2 * max([len(FEATURE_COLS), *hidden, 1]) * 4,
            "source": "manual",
        }
    else:
        best = search_max_arch(
            max_weight_kb=args.max_weight_kb,
            max_stack_bytes=args.max_stack_bytes,
        )
        hidden = best.hidden
        sizing = {
            "hidden": list(hidden),
            "n_params": best.n_params,
            "weight_kb": round(best.weight_kb, 2),
            "stack_bytes": best.stack_bytes,
            "source": "auto_search",
            "budget_weight_kb": args.max_weight_kb,
            "budget_stack_bytes": args.max_stack_bytes,
        }

    print("MAX PINN architecture for ESP32-S3")
    print(f"  hidden  = {sizing['hidden']}")
    print(f"  params  = {sizing['n_params']:,}")
    print(f"  weights = {sizing['weight_kb']} KB fp32")
    print(f"  stack   = {sizing['stack_bytes']} B")
    print("")

    df = pd.read_csv(args.data)
    model, scaler, stats = train(
        df,
        artifacts_dir=args.artifacts,
        hidden=hidden,
        epochs=args.epochs,
        lr=args.lr,
        w_phys=0.12,
        w_mono=0.04,
    )

    export_summary = export_c_header(
        model,
        scaler.mins,
        scaler.maxs,
        stats,
        args.export_header,
        header_comment="Max-size Cd PINN for ESP32-S3 (flash-backed PROGMEM weights)",
        model_tag="CD_MAX",
    )

    envelope = {
        "esp32_budget": sizing,
        "export": export_summary,
        "training_stats": stats,
        "feature_cols": FEATURE_COLS,
    }
    envelope_path = args.artifacts / "esp32_max_envelope.json"
    envelope_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    print(f"Wrote envelope: {envelope_path}")


if __name__ == "__main__":
    main()
