"""
Airbrake deployment control policy.

Converts a predicted apogee and current flight state into a discrete
deployment command for the servo actuator.

Design
------
- Stepped deployment levels: {0%, 25%, 50%, 75%, 100%}
- Proportional-to-error mapping → nearest level
- Phase gate: only deploys during coast / near-apogee
- Altitude and velocity floor guards
- Deadband to avoid chattering near target
"""
from __future__ import annotations

from enum import Enum

import numpy as np

G: float = 9.80665


class FlightPhase(str, Enum):
    GROUND = "ground"
    POWERED = "powered"
    COAST = "coast"
    NEAR_APOGEE = "near_apogee"
    DESCENT = "descent"


class DeploymentPolicy:
    """
    Stepped proportional deployment controller.

    Parameters
    ----------
    target_apogee       : mission target apogee [m]
    deadband_m          : error band within which deployment is unchanged [m]
    gain                : deployment per metre of overshoot [1/m]
    min_coast_alt_frac  : minimum altitude (fraction of target) for deployment
    min_velocity_ms     : minimum vertical velocity to allow deployment [m/s]
    """

    LEVELS: list[float] = [0.0, 0.25, 0.50, 0.75, 1.0]

    def __init__(
        self,
        target_apogee: float,
        deadband_m: float = 5.0,
        gain: float = 0.02,
        min_coast_alt_frac: float = 0.30,
        min_velocity_ms: float = 5.0,
    ) -> None:
        self.target_apogee = float(target_apogee)
        self.deadband = float(deadband_m)
        self.gain = float(gain)
        self.min_coast_h = min_coast_alt_frac * self.target_apogee
        self.min_velocity = float(min_velocity_ms)
        self._current: float = 0.0

    def reset(self) -> None:
        """Reset internal state (call at start of each flight)."""
        self._current = 0.0

    def compute_deployment(
        self,
        predicted_apogee: float,
        h: float,
        v: float,
        phase: FlightPhase,
    ) -> float:
        """
        Compute the deployment command for the current control cycle.

        Parameters
        ----------
        predicted_apogee : surrogate model output [m]
        h                : current altitude [m]
        v                : current vertical velocity [m/s]
        phase            : inferred flight phase

        Returns
        -------
        Deployment fraction in LEVELS.
        """
        # Phase and altitude / velocity guards
        if phase not in (FlightPhase.COAST, FlightPhase.NEAR_APOGEE):
            return 0.0
        if h < self.min_coast_h:
            return 0.0
        if v < self.min_velocity:
            return 0.0

        error = predicted_apogee - self.target_apogee  # positive → overshoot

        # Within deadband: hold current command
        if abs(error) < self.deadband:
            return self._current

        # Proportional mapping → clamp → nearest discrete level
        desired = float(np.clip(error * self.gain, 0.0, 1.0))
        deployment = min(self.LEVELS, key=lambda lvl: abs(lvl - desired))
        self._current = deployment
        return deployment

    @property
    def current_deployment(self) -> float:
        return self._current

    # ── Phase detection heuristic ─────────────────────────────────────────────

    @staticmethod
    def detect_phase(
        h: float,
        v: float,
        t: float,
        burnout_time: float,
        launch_altitude: float = 0.0,
    ) -> FlightPhase:
        """
        Simple heuristic phase detector.

        This does not use any ML — it operates on thresholds and can run
        on the most constrained embedded hardware.
        """
        if h <= launch_altitude + 1.0 and v < 1.0 and t < 0.5:
            return FlightPhase.GROUND
        if t < burnout_time:
            return FlightPhase.POWERED
        if v > 5.0:
            return FlightPhase.COAST
        if v > -5.0:
            return FlightPhase.NEAR_APOGEE
        return FlightPhase.DESCENT
