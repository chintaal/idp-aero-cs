"""
tests/test_pinn.py
───────────────────
Unit tests for the PINN model components.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from airbrake.models.pinn import (
    ApogeePredictor,
    FourierEmbedding,
    PINNLoss,
    PINNTrajectory,
    isa_density_torch,
)


class TestISADensityTorch:
    def test_sea_level(self):
        h = torch.tensor([0.0])
        rho = isa_density_torch(h)
        assert abs(rho.item() - 1.225) < 0.01

    def test_density_decreases(self):
        h = torch.tensor([0.0, 5_000.0, 10_000.0])
        rho = isa_density_torch(h)
        assert rho[0] > rho[1] > rho[2]

    def test_negative_altitude_clamped(self):
        h = torch.tensor([-100.0])
        rho = isa_density_torch(h)
        assert rho.item() > 0.0
        assert torch.isfinite(rho).all()

    def test_differentiable(self):
        h = torch.tensor([1_000.0], requires_grad=True)
        rho = isa_density_torch(h)
        rho.backward()
        assert h.grad is not None


class TestFourierEmbedding:
    def test_output_shape(self):
        embed = FourierEmbedding(n_freq=8)
        x = torch.randn(16)
        out = embed(x)
        assert out.shape == (16, 16)  # 2 * n_freq

    def test_output_bounded(self):
        embed = FourierEmbedding(n_freq=4)
        x = torch.randn(100) * 1000
        out = embed(x)
        assert out.abs().max() <= 1.0 + 1e-6


class TestApogeePredictor:
    @pytest.fixture
    def model(self) -> ApogeePredictor:
        return ApogeePredictor(hidden_dims=(32, 16), dropout=0.0)

    def test_output_shape(self, model):
        x = torch.randn(4, 8)
        out = model(x)
        assert out.shape == (4, 1)

    def test_forward_no_nan(self, model):
        x = torch.randn(32, 8)
        out = model(x)
        assert torch.isfinite(out).all()

    def test_eval_deterministic(self, model):
        model.eval()
        x = torch.randn(8, 8)
        with torch.no_grad():
            a = model(x)
            b = model(x)
        assert torch.allclose(a, b)

    def test_parameter_count(self, model):
        n = sum(p.numel() for p in model.parameters())
        assert n > 0

    def test_input_features_length(self):
        assert len(ApogeePredictor.INPUT_FEATURES) == 8


class TestPINNLoss:
    def test_loss_zero_residuals(self):
        loss_fn = PINNLoss(w_data=1.0, w_phys=0.1, w_ic=1.0)
        B = 16
        pred = torch.randn(B, 1)
        target = pred.clone()
        res_h = torch.zeros(B)
        res_v = torch.zeros(B)
        ic_pred = torch.randn(B, 1)
        ic_true = ic_pred.clone()
        losses = loss_fn(pred, target, res_h, res_v, ic_pred, ic_true)
        assert losses["total"].item() == pytest.approx(0.0, abs=1e-5)

    def test_all_keys_present(self):
        loss_fn = PINNLoss()
        B = 8
        zero = torch.zeros(B, 1)
        zeros_flat = torch.zeros(B)
        losses = loss_fn(zero, zero, zeros_flat, zeros_flat, zero, zero)
        assert {"total", "data", "physics", "ic"} == set(losses.keys())

    def test_total_is_weighted_sum(self):
        loss_fn = PINNLoss(w_data=2.0, w_phys=0.0, w_ic=0.0)
        B = 4
        pred = torch.ones(B, 1)
        target = torch.zeros(B, 1)
        zeros = torch.zeros(B)
        zero2 = torch.zeros(B, 1)
        losses = loss_fn(pred, target, zeros, zeros, zero2, zero2)
        # With w_phys=0, w_ic=0, total = 2 * data_loss
        expected = 2.0 * losses["data"].item()
        assert abs(losses["total"].item() - expected) < 1e-5


class TestPINNTrajectory:
    @pytest.fixture
    def model(self) -> PINNTrajectory:
        return PINNTrajectory(hidden_dims=(32, 32), n_freq=4)

    def test_output_shape(self, model):
        B = 8
        tau = torch.rand(B)
        ctx = torch.randn(B, PINNTrajectory.N_CONTEXT)
        out = model(tau, ctx)
        assert out.shape == (B, 2)

    def test_physics_residuals_finite(self, model):
        B = 4
        tau = torch.rand(B)
        ctx = torch.abs(torch.randn(B, PINNTrajectory.N_CONTEXT))
        ctx[:, 5] = 5.0  # T_coast
        R_h, R_v = model.physics_residual(tau, ctx)
        assert torch.isfinite(R_h).all()
        assert torch.isfinite(R_v).all()
