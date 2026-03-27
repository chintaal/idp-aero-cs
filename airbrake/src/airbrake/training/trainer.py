"""
Training loop for the PINN ApogeePredictor.

Features
--------
- AdamW optimiser with cosine annealing LR schedule
- Huber loss (robust to outlier apogee values)
- Gradient clipping for stability
- Early stopping on validation loss
- Checkpoint saving (best model only)
- Training history export to JSON for plotting
- Feature min-max scaling + target z-score normalisation

Quick start
-----------
    from airbrake.training.trainer import train_apogee_predictor
    model = train_apogee_predictor(train_df, val_df, Path("artifacts/"))
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from ..models.pinn import ApogeePredictor
from .dataset import FEATURE_COLS, TARGET_COL, FeatureScaler

logger = logging.getLogger(__name__)


def train_apogee_predictor(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    artifacts_dir: Path,
    # ── Architecture ──────────────────────────────────────────────────────────
    hidden_dims: tuple[int, ...] = (128, 128, 64, 32),
    dropout: float = 0.10,
    # ── Optimisation ──────────────────────────────────────────────────────────
    epochs: int = 150,
    batch_size: int = 512,
    lr: float = 3e-4,
    weight_decay: float = 1e-4,
    patience: int = 20,
    device: Optional[str] = None,
) -> ApogeePredictor:
    """
    Train the PINN surrogate apogee predictor.

    Parameters
    ----------
    train_df / val_df : DataFrames produced by physics.simulation.generate_dataset()
    artifacts_dir     : directory where weights, scaler, and stats are saved
    hidden_dims       : MLP layer sizes
    dropout           : dropout probability in each hidden block
    epochs            : maximum training epochs
    batch_size        : mini-batch size
    lr                : initial learning rate for AdamW
    weight_decay      : L2 regularisation for AdamW
    patience          : early-stopping patience (epochs without val improvement)
    device            : 'cpu' | 'cuda' | None  (auto-detect if None)

    Returns
    -------
    Trained ApogeePredictor (best checkpoint loaded).

    Artefacts written to artifacts_dir
    ------------------------------------
    pinn_best.pt           model weights (best val loss)
    feature_scaler.pkl     FeatureScaler (min-max normalisation)
    target_stats.json      {"mean": …, "std": …} for output de-normalisation
    training_history.json  epoch-level metrics for plotting
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    dev = torch.device(device)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Training PINN  |  device=%s  |  train=%d  val=%d",
        device, len(train_df), len(val_df),
    )

    # ── Feature scaling ───────────────────────────────────────────────────────
    scaler = FeatureScaler()
    X_train = scaler.fit_transform(train_df[FEATURE_COLS].values.astype(np.float32))
    X_val = scaler.transform(val_df[FEATURE_COLS].values.astype(np.float32))
    joblib.dump(scaler, artifacts_dir / "feature_scaler.pkl")

    # ── Target normalisation ──────────────────────────────────────────────────
    y_train_raw = train_df[TARGET_COL].values.astype(np.float32).reshape(-1, 1)
    y_val_raw = val_df[TARGET_COL].values.astype(np.float32).reshape(-1, 1)
    y_mean = float(y_train_raw.mean())
    y_std = float(y_train_raw.std()) + 1e-8
    y_train = (y_train_raw - y_mean) / y_std
    y_val = (y_val_raw - y_mean) / y_std

    with open(artifacts_dir / "target_stats.json", "w") as f:
        json.dump({"mean": y_mean, "std": y_std}, f, indent=2)

    # ── Tensors & loaders ─────────────────────────────────────────────────────
    X_tr = torch.from_numpy(X_train).to(dev)
    y_tr = torch.from_numpy(y_train).to(dev)
    X_va = torch.from_numpy(X_val).to(dev)
    y_va = torch.from_numpy(y_val).to(dev)

    loader = DataLoader(
        TensorDataset(X_tr, y_tr),
        batch_size=batch_size,
        shuffle=True,
        drop_last=False,
    )

    # ── Model, optimiser, scheduler ───────────────────────────────────────────
    model = ApogeePredictor(hidden_dims=hidden_dims, dropout=dropout).to(dev)
    optimiser = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimiser, T_max=epochs, eta_min=lr * 0.01)
    criterion = nn.HuberLoss()

    # ── Training loop ─────────────────────────────────────────────────────────
    best_val_loss = float("inf")
    no_improve = 0
    history: list[dict] = []

    for epoch in range(1, epochs + 1):
        # Train
        model.train()
        train_losses: list[float] = []
        for X_b, y_b in loader:
            optimiser.zero_grad()
            loss = criterion(model(X_b), y_b)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimiser.step()
            train_losses.append(loss.item())

        # Validate
        model.eval()
        with torch.no_grad():
            val_pred_norm = model(X_va)
            val_loss = criterion(val_pred_norm, y_va).item()
            # MAE in real metres
            val_pred_m = val_pred_norm.cpu().numpy() * y_std + y_mean
            val_mae_m = float(np.abs(val_pred_m - y_val_raw).mean())

        scheduler.step()

        mean_train = float(np.mean(train_losses))
        current_lr = float(optimiser.param_groups[0]["lr"])
        history.append({
            "epoch": epoch,
            "train_loss": mean_train,
            "val_loss": val_loss,
            "val_mae_m": val_mae_m,
            "lr": current_lr,
        })

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            no_improve = 0
            torch.save(model.state_dict(), artifacts_dir / "pinn_best.pt")

        else:
            no_improve += 1

        if epoch % 10 == 0 or epoch == 1:
            logger.info(
                "Epoch %3d/%d  |  train=%.5f  val=%.5f  MAE=%.1f m  lr=%.2e",
                epoch, epochs, mean_train, val_loss, val_mae_m, current_lr,
            )

        if no_improve >= patience:
            logger.info("Early stopping triggered at epoch %d  (best val=%.5f)", epoch, best_val_loss)
            break

    # Save full history
    with open(artifacts_dir / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)

    # Load best checkpoint before returning
    model.load_state_dict(
        torch.load(artifacts_dir / "pinn_best.pt", map_location=dev, weights_only=True)
    )
    logger.info("Training complete.  Best val loss = %.5f  MAE ≈ %.1f m", best_val_loss, history[-1]["val_mae_m"])
    return model
