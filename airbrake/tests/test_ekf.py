"""
tests/test_ekf.py
──────────────────
Unit tests for the Extended Kalman Filter.
"""
from __future__ import annotations

import numpy as np
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from airbrake.estimation.ekf import RocketEKF


class TestEKF:
    @pytest.fixture
    def ekf(self) -> RocketEKF:
        ekf = RocketEKF(q_h=0.1, q_v=0.5, r_baro=4.0, r_accel=0.09)
        ekf.reset(h0=100.0, v0=50.0)
        return ekf

    def test_initial_state(self, ekf):
        assert ekf.altitude == pytest.approx(100.0)
        assert ekf.velocity == pytest.approx(50.0)

    def test_predict_advances_state(self, ekf):
        dt = 0.05
        g = 9.80665
        initial_v = ekf.velocity
        ekf.predict(imu_accel=-g, dt=dt)
        # Velocity should decrease due to gravity
        assert ekf.velocity < initial_v

    def test_predict_altitude_increases_with_positive_velocity(self):
        ekf = RocketEKF()
        ekf.reset(h0=200.0, v0=30.0)
        ekf.predict(imu_accel=0.0, dt=0.1)
        assert ekf.altitude > 200.0

    def test_baro_update_corrects_altitude(self, ekf):
        # Move state far from truth
        ekf.state.h = 200.0
        ekf.update_baro(100.0)  # true altitude is 100
        # After update, estimate should shift toward 100
        assert ekf.altitude < 200.0

    def test_covariance_positive_definite(self, ekf):
        for _ in range(20):
            ekf.predict(imu_accel=-9.8, dt=0.05)
            ekf.update_baro(ekf.altitude + np.random.normal(0, 2))
        eigenvalues = np.linalg.eigvalsh(ekf.covariance)
        assert np.all(eigenvalues > 0), "Covariance is not positive-definite"

    def test_covariance_decreases_after_update(self):
        """Baro update should reduce altitude uncertainty."""
        ekf = RocketEKF(r_baro=0.01)  # very precise barometer
        ekf.reset(h0=0.0, v0=100.0)
        trace_before = np.trace(ekf.covariance)
        ekf.update_baro(0.0)
        trace_after = np.trace(ekf.covariance)
        assert trace_after < trace_before

    def test_uncertainty_properties(self, ekf):
        assert ekf.altitude_std > 0.0
        assert ekf.velocity_std > 0.0

    def test_reset_clears_state(self, ekf):
        ekf.predict(-9.8, 0.05)
        ekf.reset(h0=0.0, v0=0.0)
        assert ekf.altitude == pytest.approx(0.0)
        assert ekf.velocity == pytest.approx(0.0)

    def test_tracking_noisy_barometer(self):
        """EKF should track a smoothly rising altitude despite baro noise."""
        ekf = RocketEKF()
        ekf.reset(h0=0.0, v0=50.0)
        rng = np.random.default_rng(42)

        true_h, true_v = 0.0, 50.0
        errors = []
        for _ in range(100):
            dt = 0.05
            true_v -= 9.80665 * dt
            true_h += true_v * dt
            noisy_baro = true_h + rng.normal(0, 2.0)
            ekf.predict(imu_accel=-9.80665, dt=dt)
            ekf.update_baro(noisy_baro)
            errors.append(abs(ekf.altitude - true_h))

        # Average tracking error should be well under 10 m
        assert np.mean(errors) < 10.0
