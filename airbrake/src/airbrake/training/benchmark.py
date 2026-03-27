"""
Multi-model benchmark: evaluate all trained models on the held-out test set.

Metrics
-------
MAE   — mean absolute error [m]        (primary)
RMSE  — root-mean-square error [m]
R²    — coefficient of determination
p95   — 95th-percentile absolute error [m]
lat   — per-sample inference latency   [µs]

Usage
-----
    from airbrake.training.benchmark import benchmark_all
    results_df = benchmark_all(test_df, artifacts_dir=Path("artifacts/"))
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ..models.baselines import FEATURE_COLS, TARGET_COL
from ..physics.rocket import analytical_ballistic_apogee

logger = logging.getLogger(__name__)


# ── Individual evaluators ─────────────────────────────────────────────────────

def _eval_sklearn(name: str, model, X: np.ndarray, y: np.ndarray) -> dict:
    t0 = time.perf_counter()
    pred = model.predict(X)
    elapsed_s = time.perf_counter() - t0

    return _metrics(name, pred, y, elapsed_s, len(X))


def _eval_pinn(
    artifacts_dir: Path,
    X_raw: np.ndarray,
    y: np.ndarray,
) -> dict | None:
    """Evaluate the PINN checkpoint if available."""
    from ..models.pinn import ApogeePredictor

    pinn_path = artifacts_dir / "pinn_best.pt"
    scaler_path = artifacts_dir / "feature_scaler.pkl"
    stats_path = artifacts_dir / "target_stats.json"

    if not (pinn_path.exists() and scaler_path.exists() and stats_path.exists()):
        logger.warning("PINN artefacts not found — skipping PINN evaluation.")
        return None

    scaler = joblib.load(scaler_path)
    with open(stats_path) as f:
        stats = json.load(f)

    model = ApogeePredictor()
    model.load_state_dict(torch.load(pinn_path, map_location="cpu", weights_only=True))
    model.eval()

    X_scaled = scaler.transform(X_raw.astype(np.float32))
    X_t = torch.from_numpy(X_scaled)

    t0 = time.perf_counter()
    with torch.no_grad():
        pred_norm = model(X_t).numpy().flatten()
    elapsed_s = time.perf_counter() - t0

    pred = pred_norm * stats["std"] + stats["mean"]
    return _metrics("pinn", pred, y, elapsed_s, len(X_raw))


def _eval_ballistic_baseline(X_raw: np.ndarray, y: np.ndarray) -> dict:
    """Drag-free analytical baseline: h_apogee = h + v²/(2g)."""
    # Columns: h, v, a, deployment, rho, t_since_burnout, mass_dry, A_ref, Cd_total
    h_col = X_raw[:, 0]
    v_col = X_raw[:, 1]
    pred = np.array([analytical_ballistic_apogee(h, v) for h, v in zip(h_col, v_col)])
    return _metrics("ballistic_baseline", pred, y, elapsed_s=0.0, n=len(X_raw))


def _metrics(name: str, pred: np.ndarray, y: np.ndarray, elapsed_s: float, n: int) -> dict:
    mae = mean_absolute_error(y, pred)
    rmse = float(np.sqrt(mean_squared_error(y, pred)))
    r2 = float(r2_score(y, pred))
    p95 = float(np.percentile(np.abs(pred - y), 95))
    lat_us = (elapsed_s / max(n, 1)) * 1e6
    return {
        "model": name,
        "mae_m": round(mae, 3),
        "rmse_m": round(rmse, 3),
        "r2": round(r2, 4),
        "p95_m": round(p95, 3),
        "latency_us": round(lat_us, 2),
    }


# ── Main benchmark entry point ────────────────────────────────────────────────

def benchmark_all(
    test_df: pd.DataFrame,
    artifacts_dir: Path,
    output_csv: Path | None = None,
) -> pd.DataFrame:
    """
    Evaluate all available trained models on *test_df* and return a summary.

    Parameters
    ----------
    test_df       : held-out test DataFrame (FEATURE_COLS + TARGET_COL)
    artifacts_dir : directory containing saved model artefacts
    output_csv    : if provided, write results CSV to this path

    Returns
    -------
    pd.DataFrame  sorted by MAE ascending.
    """
    artifacts_dir = Path(artifacts_dir)
    X = test_df[FEATURE_COLS].values
    y = test_df[TARGET_COL].values

    results: list[dict] = []

    # ── Analytical baseline (always available) ────────────────────────────────
    results.append(_eval_ballistic_baseline(X, y))

    # ── Sklearn / GBDT baselines ──────────────────────────────────────────────
    baseline_files = {
        "ridge": "ridge_model.pkl",
        "decision_tree": "decision_tree_model.pkl",
        "extra_trees": "extra_trees_model.pkl",
        "adaboost": "adaboost_model.pkl",
        "lightgbm": "lightgbm_model.pkl",
        "catboost": "catboost_model.pkl",
    }
    for name, fname in baseline_files.items():
        path = artifacts_dir / fname
        if path.exists():
            model = joblib.load(path)
            results.append(_eval_sklearn(name, model, X, y))
        else:
            logger.debug("Skipping %s — %s not found", name, fname)

    # ── PINN ──────────────────────────────────────────────────────────────────
    pinn_result = _eval_pinn(artifacts_dir, X, y)
    if pinn_result:
        results.append(pinn_result)

    # ── Summary table ─────────────────────────────────────────────────────────
    df = pd.DataFrame(results).sort_values("mae_m").reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))

    logger.info("\n%s\n", df.to_string(index=False))

    if output_csv is not None:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        with open(output_csv.with_suffix(".json"), "w") as f:
            json.dump(results, f, indent=2)
        logger.info("Results saved to %s", output_csv)

    return df
