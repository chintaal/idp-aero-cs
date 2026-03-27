"""Training sub-package: datasets, PINN trainer, and benchmarking."""

from .dataset import ApogeeDataset, FeatureScaler, FEATURE_COLS, TARGET_COL, make_dataloader
from .trainer import train_apogee_predictor
from .benchmark import benchmark_all

__all__ = [
    "ApogeeDataset", "FeatureScaler", "FEATURE_COLS", "TARGET_COL", "make_dataloader",
    "train_apogee_predictor",
    "benchmark_all",
]
