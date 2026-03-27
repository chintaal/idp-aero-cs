"""
Model registry — loads and manages all inference-ready models.

The registry is the single entry point used by the FastAPI server to
perform apogee predictions without knowing which model is active.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch

from .pinn import ApogeePredictor

logger = logging.getLogger(__name__)

#: Features consumed in the same order as ApogeePredictor.INPUT_FEATURES
_FEATURE_ORDER: list[str] = [
    "h", "v", "deployment", "rho",
    "t_since_burnout", "mass_dry", "A_ref", "Cd_total",
]


class ModelRegistry:
    """
    Loads and routes inference requests to the best available model.

    Priority: PINN checkpoint  >  LightGBM pkl  >  (none — 503 from API)

    All model artefacts are stored under *artifacts_dir*:
        pinn_best.pt           — PyTorch PINN weights
        feature_scaler.pkl     — FeatureScaler for PINN inputs
        target_stats.json      — {"mean": …, "std": …} for PINN outputs
        lightgbm_model.pkl     — fallback LightGBM model
    """

    def __init__(self, artifacts_dir: Path) -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self._model: Any = None
        self._scaler: Any = None
        self._target_stats: dict = {}
        self._model_name: str = "none"
        self.is_loaded: bool = False

    # ── Loading ───────────────────────────────────────────────────────────────

    def load_default(self) -> None:
        """Attempt to load the best available model from artifacts_dir."""
        pinn_path = self.artifacts_dir / "pinn_best.pt"
        scaler_path = self.artifacts_dir / "feature_scaler.pkl"
        stats_path = self.artifacts_dir / "target_stats.json"
        lgbm_path = self.artifacts_dir / "lightgbm_model.pkl"

        if pinn_path.exists() and scaler_path.exists() and stats_path.exists():
            self._load_pinn(pinn_path, scaler_path, stats_path)
        elif lgbm_path.exists():
            self._load_sklearn("lightgbm", lgbm_path)
        else:
            logger.warning(
                "No trained model found in %s — run 'make train-pinn' first.",
                self.artifacts_dir,
            )

    def _load_pinn(
        self, pinn_path: Path, scaler_path: Path, stats_path: Path
    ) -> None:
        model = ApogeePredictor()
        model.load_state_dict(
            torch.load(pinn_path, map_location="cpu", weights_only=True)
        )
        model.eval()
        self._model = model
        self._scaler = joblib.load(scaler_path)
        with open(stats_path) as f:
            self._target_stats = json.load(f)
        self._model_name = "pinn"
        self.is_loaded = True
        logger.info("Registry: loaded PINN from %s", pinn_path)

    def _load_sklearn(self, name: str, path: Path) -> None:
        self._model = joblib.load(path)
        self._model_name = name
        self.is_loaded = True
        logger.info("Registry: loaded %s from %s", name, path)

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict_apogee(self, state: Any) -> float:
        """
        Predict apogee from a FlightState-like object (has the feature attributes).

        Parameters
        ----------
        state : object with attributes matching _FEATURE_ORDER

        Returns
        -------
        Predicted apogee altitude [m].
        """
        if not self.is_loaded:
            raise RuntimeError("No model loaded. Run load_default() first.")

        row = np.array(
            [[getattr(state, col, 0.0) for col in _FEATURE_ORDER]],
            dtype=np.float32,
        )

        if self._model_name == "pinn":
            return self._predict_pinn(row)
        return float(self._model.predict(row)[0])

    def _predict_pinn(self, row: np.ndarray) -> float:
        X_scaled = self._scaler.transform(row)
        X_t = torch.from_numpy(X_scaled)
        with torch.no_grad():
            pred_norm = self._model(X_t).item()
        mean = self._target_stats["mean"]
        std = self._target_stats["std"]
        return float(pred_norm * std + mean)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def active_model_name(self) -> str:
        return self._model_name
