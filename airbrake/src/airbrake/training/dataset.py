"""
PyTorch datasets, scalers, and DataLoader helpers for PINN training.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset

from ..physics.simulation import FEATURE_COLS, TARGET_COL

__all__ = [
    "FEATURE_COLS", "TARGET_COL",
    "ApogeeDataset", "FeatureScaler", "make_dataloader",
]


class ApogeeDataset(Dataset):
    """
    PyTorch Dataset wrapping a pandas DataFrame of flight state snapshots.

    Each item is  (feature_vector: Tensor[8], apogee: Tensor[1]).
    """

    def __init__(
        self,
        df: pd.DataFrame,
        feature_cols: list[str] = FEATURE_COLS,
        target_col: str = TARGET_COL,
    ) -> None:
        X = df[feature_cols].values.astype(np.float32)
        y = df[target_col].values.astype(np.float32).reshape(-1, 1)
        self.X = torch.from_numpy(X)
        self.y = torch.from_numpy(y)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]


class FeatureScaler:
    """
    Per-feature min-max scaler that maps each column to [0, 1].

    A simple numeric scaler is used instead of sklearn's StandardScaler so
    the scaler state can be serialised to a plain numpy dict (and loaded
    without sklearn during embedded inference if required).
    """

    def __init__(self) -> None:
        self.mins: Optional[np.ndarray] = None
        self.maxs: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> "FeatureScaler":
        self.mins = X.min(axis=0)
        self.maxs = X.max(axis=0)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        assert self.mins is not None, "Scaler not fitted. Call fit() first."
        rng = self.maxs - self.mins
        rng = np.where(rng < 1e-10, 1.0, rng)  # avoid division by zero
        return (X - self.mins) / rng

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        assert self.mins is not None
        rng = self.maxs - self.mins
        rng = np.where(rng < 1e-10, 1.0, rng)
        return X * rng + self.mins


def make_dataloader(
    df: pd.DataFrame,
    feature_cols: list[str] = FEATURE_COLS,
    batch_size: int = 512,
    shuffle: bool = True,
    num_workers: int = 0,
) -> DataLoader:
    """Convenience wrapper: DataFrame → DataLoader."""
    dataset = ApogeeDataset(df, feature_cols=feature_cols)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
    )
