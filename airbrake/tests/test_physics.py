"""
tests/test_physics.py
──────────────────────
Unit tests for the ISA atmosphere model, rocket EOM, and simulation pipeline.
"""
from __future__ import annotations

import numpy as np
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from airbrake.physics.atmosphere import density, pressure, temperature, density_vec
from airbrake.physics.rocket import RocketParams, analytical_ballistic_apogee, derivatives
from airbrake.physics.simulation import generate_dataset, simulate_flight, split_by_flight


# ── Atmosphere ────────────────────────────────────────────────────────────────

class TestISA:
    def test_sea_level_temperature(self):
        assert abs(temperature(0) - 288.15) < 0.01

    def test_sea_level_pressure(self):
        assert abs(pressure(0) - 101_325.0) < 1.0

    def test_sea_level_density(self):
        assert abs(density(0) - 1.225) < 0.01

    def test_density_decreases_with_altitude(self):
        assert density(1_000) < density(0)
        assert density(5_000) < density(1_000)
        assert density(10_000) < density(5_000)

    def test_tropopause_transition(self):
        # Density should be continuous across the tropopause (~11 km)
        rho_below = density(10_999.0)
        rho_above = density(11_001.0)
        assert abs(rho_below - rho_above) / rho_below < 0.01  # <1% jump

    def test_vectorised_matches_scalar(self):
        altitudes = np.array([0.0, 500.0, 5_000.0, 11_000.0, 15_000.0])
        vec = density_vec(altitudes)
        scalar = np.array([density(h) for h in altitudes])
        np.testing.assert_allclose(vec, scalar, rtol=1e-9)

    def test_negative_altitude_clamped(self):
        # density_vec should handle slightly negative altitudes gracefully
        rho = density_vec(np.array([-10.0, 0.0]))
        assert np.all(np.isfinite(rho))


# ── Rocket parameters ─────────────────────────────────────────────────────────

class TestRocketParams:
    @pytest.fixture
    def params(self) -> RocketParams:
        return RocketParams(
            mass_wet=1.5,
            mass_propellant=0.3,
            A_ref=0.002,
            Cd_body=0.55,
            Cd_brake_max=0.80,
            burn_time=2.0,
            total_impulse=100.0,
        )

    def test_mass_dry(self, params):
        assert abs(params.mass_dry - 1.2) < 1e-9

    def test_mean_thrust(self, params):
        assert abs(params.mean_thrust - 50.0) < 1e-9

    def test_thrust_during_burn(self, params):
        assert params.thrust(1.0) == pytest.approx(50.0)

    def test_thrust_after_burn(self, params):
        assert params.thrust(2.5) == 0.0

    def test_mass_decreases_during_burn(self, params):
        assert params.mass_at(1.0) < params.mass_at(0.0)
        assert params.mass_at(2.0) == pytest.approx(params.mass_dry, rel=1e-6)

    def test_cd_at_full_deployment(self, params):
        assert abs(params.Cd_at(1.0) - (0.55 + 0.80)) < 1e-9

    def test_cd_at_zero_deployment(self, params):
        assert abs(params.Cd_at(0.0) - 0.55) < 1e-9


# ── Simulation ────────────────────────────────────────────────────────────────

class TestSimulation:
    @pytest.fixture
    def default_params(self) -> RocketParams:
        return RocketParams(
            mass_wet=1.5, mass_propellant=0.3, A_ref=0.002,
            Cd_body=0.55, Cd_brake_max=0.80, burn_time=2.0, total_impulse=100.0,
        )

    def test_apogee_positive(self, default_params):
        traj = simulate_flight(default_params)
        assert traj.apogee > 0.0

    def test_apogee_below_ballistic(self, default_params):
        traj = simulate_flight(default_params)
        # Drag should always make true apogee lower than drag-free estimate
        # Use burnout conditions as a rough check
        burnout_idx = int(traj.t.searchsorted(default_params.burn_time))
        h_bo = float(traj.h[burnout_idx])
        v_bo = float(traj.v[burnout_idx])
        ballistic = analytical_ballistic_apogee(h_bo, v_bo)
        assert traj.apogee < ballistic

    def test_deployment_reduces_apogee(self, default_params):
        traj_no = simulate_flight(default_params, deployment=0.0)
        traj_full = simulate_flight(default_params, deployment=1.0)
        assert traj_full.apogee < traj_no.apogee

    def test_trajectory_time_monotonic(self, default_params):
        traj = simulate_flight(default_params)
        assert np.all(np.diff(traj.t) > 0)


# ── Dataset generation ────────────────────────────────────────────────────────

class TestDatasetGeneration:
    def test_generates_rows(self):
        df = generate_dataset(n_flights=50, samples_per_flight=5, seed=1)
        assert len(df) > 0

    def test_required_columns_present(self):
        df = generate_dataset(n_flights=20, samples_per_flight=3, seed=2)
        expected = {"h", "v", "a", "deployment", "rho", "t_since_burnout",
                    "mass_dry", "A_ref", "Cd_total", "target_apogee", "flight_id"}
        assert expected.issubset(set(df.columns))

    def test_target_apogee_positive(self):
        df = generate_dataset(n_flights=20, samples_per_flight=3, seed=3)
        assert (df["target_apogee"] > 0).all()

    def test_split_no_leakage(self):
        df = generate_dataset(n_flights=100, samples_per_flight=5, seed=4)
        train, val, test = split_by_flight(df, seed=4)
        train_ids = set(train["flight_id"])
        val_ids = set(val["flight_id"])
        test_ids = set(test["flight_id"])
        assert train_ids.isdisjoint(val_ids)
        assert train_ids.isdisjoint(test_ids)
        assert val_ids.isdisjoint(test_ids)

    def test_split_covers_all_flights(self):
        df = generate_dataset(n_flights=60, samples_per_flight=5, seed=5)
        train, val, test = split_by_flight(df, seed=5)
        all_ids = set(df["flight_id"])
        covered = set(train["flight_id"]) | set(val["flight_id"]) | set(test["flight_id"])
        assert covered == all_ids
