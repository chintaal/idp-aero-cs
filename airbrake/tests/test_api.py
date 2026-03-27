"""
tests/test_api.py
──────────────────
Integration tests for the FastAPI endpoints using httpx.AsyncClient.

The model registry is mocked so tests run without trained artefacts.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def client():
    """TestClient with a mocked model registry pre-loaded in app.state."""
    from airbrake.api.main import app

    mock_registry = MagicMock()
    mock_registry.is_loaded = True
    mock_registry.active_model_name = "pinn"
    mock_registry.predict_apogee.return_value = 312.5

    # Inject AFTER the lifespan has run (lifespan overwrites app.state.registry
    # with a real ModelRegistry; we replace it here before tests execute).
    with TestClient(app, raise_server_exceptions=True) as c:
        app.state.registry = mock_registry
        yield c


class TestHealthEndpoint:
    def test_health_ok(self, client):
        resp = client.get("/health/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["model_loaded"] is True
        assert data["active_model"] == "pinn"


class TestPredictApogee:
    def test_valid_state_returns_prediction(self, client):
        payload = {
            "h": 150.0,
            "v": 45.0,
            "t_since_burnout": 2.0,
            "deployment": 0.0,
        }
        resp = client.post("/predict/apogee", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "predicted_apogee_m" in data
        assert data["predicted_apogee_m"] == pytest.approx(312.5)
        assert data["model_used"] == "pinn"

    def test_missing_required_field_422(self, client):
        # 'h' and 'v' are required; omitting 'v'
        payload = {"h": 150.0, "t_since_burnout": 1.0}
        resp = client.post("/predict/apogee", json=payload)
        assert resp.status_code == 422

    def test_altitude_out_of_range_422(self, client):
        payload = {"h": -100.0, "v": 50.0, "t_since_burnout": 1.0}
        resp = client.post("/predict/apogee", json=payload)
        assert resp.status_code == 422

    def test_rho_auto_filled(self, client):
        """rho is optional — omitting it should still succeed."""
        payload = {"h": 200.0, "v": 30.0, "t_since_burnout": 3.0}
        resp = client.post("/predict/apogee", json=payload)
        assert resp.status_code == 200


class TestDeploymentEndpoint:
    def test_overshoot_returns_nonzero_deployment(self, client):
        payload = {
            "predicted_apogee_m": 350.0,
            "target_apogee_m": 300.0,
            "h": 200.0,
            "v": 20.0,
            "phase": "coast",
        }
        resp = client.post("/predict/deployment", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["deployment_fraction"] > 0.0
        assert data["apogee_error_m"] == pytest.approx(50.0)

    def test_undershoot_returns_zero_deployment(self, client):
        payload = {
            "predicted_apogee_m": 250.0,
            "target_apogee_m": 300.0,
            "h": 200.0,
            "v": 20.0,
            "phase": "coast",
        }
        resp = client.post("/predict/deployment", json=payload)
        assert resp.status_code == 200
        assert resp.json()["deployment_fraction"] == 0.0

    def test_invalid_phase_422(self, client):
        payload = {
            "predicted_apogee_m": 350.0,
            "target_apogee_m": 300.0,
            "h": 200.0,
            "v": 20.0,
            "phase": "banana",
        }
        resp = client.post("/predict/deployment", json=payload)
        assert resp.status_code == 422

    def test_powered_phase_zero_deployment(self, client):
        payload = {
            "predicted_apogee_m": 500.0,
            "target_apogee_m": 300.0,
            "h": 100.0,
            "v": 80.0,
            "phase": "powered",
        }
        resp = client.post("/predict/deployment", json=payload)
        assert resp.status_code == 200
        assert resp.json()["deployment_fraction"] == 0.0


class TestSimulationEndpoint:
    def test_basic_simulation(self, client):
        payload = {
            "mass_wet": 1.5,
            "mass_propellant": 0.3,
            "A_ref": 0.002,
            "Cd_body": 0.55,
            "Cd_brake_max": 0.80,
            "burn_time": 2.0,
            "total_impulse": 100.0,
            "deployment": 0.0,
        }
        resp = client.post("/simulate/trajectory", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["apogee_m"] > 0.0
        assert data["apogee_time_s"] > 0.0
        assert data["trajectory_points"] > 10

    def test_deployment_reduces_apogee(self, client):
        base = {
            "mass_wet": 1.5, "mass_propellant": 0.3, "A_ref": 0.002,
            "Cd_body": 0.55, "Cd_brake_max": 0.80,
            "burn_time": 2.0, "total_impulse": 100.0,
        }
        resp_no = client.post("/simulate/trajectory", json={**base, "deployment": 0.0})
        resp_full = client.post("/simulate/trajectory", json={**base, "deployment": 1.0})
        assert resp_no.json()["apogee_m"] > resp_full.json()["apogee_m"]

    def test_propellant_ge_wet_mass_422(self, client):
        payload = {
            "mass_wet": 1.0, "mass_propellant": 1.5,
            "A_ref": 0.002, "Cd_body": 0.55, "Cd_brake_max": 0.8,
            "burn_time": 2.0, "total_impulse": 100.0,
        }
        resp = client.post("/simulate/trajectory", json=payload)
        assert resp.status_code == 422
