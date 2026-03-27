"""
Physics-Informed Neural Network (PINN) components for apogee prediction.

Two complementary models are provided:

ApogeePredictor (surrogate model)
    A compact MLP that maps a coast-phase flight state snapshot directly to
    predicted final apogee.  Uses SiLU activations and LayerNorm for stable
    training on normalised aerodynamic inputs.

PINNTrajectory (physics-constrained trajectory model)
    A network that learns  [h(τ), v(τ)]  — the coast-phase trajectory
    parameterised by normalised time τ ∈ [0, 1].  Physics residuals are
    enforced via automatic differentiation:

        dh/dτ  =  v · T_coast                                       (kinematic)
        dv/dτ  =  [-g − sign(v)·(ρ v² Cd A)/(2m)] · T_coast       (force balance)

    The PINNTrajectory can be used during training to regularise the
    ApogeePredictor and also as a physics-grounded consistency check.

PINNLoss
    Combined loss: data MSE + physics residual MSE + initial-condition loss.
"""
from __future__ import annotations

from typing import Tuple

import torch
import torch.autograd as autograd
import torch.nn as nn

# ── Physical constants (must match physics/atmosphere.py) ────────────────────
G: float = 9.80665
R_AIR: float = 287.058
T0: float = 288.15
P0: float = 101_325.0
L: float = 0.0065
H_TROP: float = 11_000.0
T_TROP: float = 216.65
P_TROP: float = 22_632.1
_EXP: float = G / (L * R_AIR)  # ≈ 5.256


# ── Differentiable ISA density ────────────────────────────────────────────────

def isa_density_torch(h: torch.Tensor) -> torch.Tensor:
    """
    Differentiable ISA air density suitable for autograd-based PINN losses.

    Parameters
    ----------
    h : altitude tensor [m]

    Returns
    -------
    density tensor [kg/m³]
    """
    h = h.clamp(min=0.0)
    T = torch.where(h < H_TROP, T0 - L * h, h.new_full(h.shape, T_TROP))
    P = torch.where(
        h < H_TROP,
        P0 * (T / T0) ** _EXP,
        P_TROP * torch.exp(-G * (h - H_TROP).clamp(min=0.0) / (R_AIR * T_TROP)),
    )
    return P / (R_AIR * T)


# ── Fourier feature embedding ─────────────────────────────────────────────────

class FourierEmbedding(nn.Module):
    """
    Random Fourier feature embedding for improved frequency representation.

    Maps a scalar input x → [sin(ω₁x), cos(ω₁x), …, sin(ωₙx), cos(ωₙx)]
    using log-spaced frequencies, which helps the PINN resolve both slow
    and fast oscillations in the trajectory.
    """

    def __init__(self, n_freq: int = 8) -> None:
        super().__init__()
        freqs = 2.0 ** torch.arange(0, n_freq, dtype=torch.float32)
        self.register_buffer("freqs", freqs)
        self._n_freq = n_freq

    @property
    def out_dim(self) -> int:
        return 2 * self._n_freq

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B,) → (B, 2·n_freq)."""
        scaled = x.unsqueeze(-1) * self.freqs  # (B, n_freq)
        return torch.cat([torch.sin(scaled), torch.cos(scaled)], dim=-1)


# ── Surrogate apogee predictor ────────────────────────────────────────────────

class ApogeePredictor(nn.Module):
    """
    Surrogate MLP that predicts final apogee from a coast-phase state snapshot.

    Input features (8 total):
        h, v, deployment, rho, t_since_burnout, mass_dry, A_ref, Cd_total

    Output:
        predicted apogee h_apogee  [m]  (scalar, normalised during training)

    Architecture
    ------------
    Linear → LayerNorm → SiLU → Dropout  (repeated per hidden layer)
    Final linear head → scalar output

    SiLU (Swish) is preferred over ReLU for physics-based tasks because it
    is smooth and has non-zero gradients for negative inputs, which helps
    the network model the near-apogee regime where velocity approaches zero.
    """

    #: Feature column order — must match dataset construction
    INPUT_FEATURES: list[str] = [
        "h", "v", "deployment", "rho",
        "t_since_burnout", "mass_dry", "A_ref", "Cd_total",
    ]

    def __init__(
        self,
        hidden_dims: tuple[int, ...] = (128, 128, 64, 32),
        dropout: float = 0.10,
    ) -> None:
        super().__init__()
        in_dim = len(self.INPUT_FEATURES)
        layers: list[nn.Module] = []
        prev = in_dim
        for h_dim in hidden_dims:
            layers += [
                nn.Linear(prev, h_dim),
                nn.LayerNorm(h_dim),
                nn.SiLU(),
                nn.Dropout(dropout),
            ]
            prev = h_dim
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)
        self._init_weights()

    def _init_weights(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, 8) → (B, 1)  normalised apogee prediction."""
        return self.net(x)


# ── Physics-constrained trajectory network ────────────────────────────────────

class PINNTrajectory(nn.Module):
    """
    PINN that models the coast-phase trajectory  h(τ), v(τ)  for τ ∈ [0, 1].

    Context vector (6 values):
        [h_burnout, v_burnout, Cd, A_ref, mass, T_coast]

    The network takes (τ, context) and outputs [h(τ), v(τ)].

    Physics residuals (computed via autograd during training):
        R_h = dh/dτ − v · T_coast                          → 0
        R_v = dv/dτ − [−g − sign(v)·drag_accel] · T_coast → 0

    The Tanh activation is standard for PINN trajectory networks because it
    is smooth, bounded, and has well-defined second derivatives.
    """

    N_CONTEXT: int = 6  # [h0, v0, Cd, A_ref, mass, T_coast]

    def __init__(
        self,
        hidden_dims: tuple[int, ...] = (64, 128, 128, 64),
        n_freq: int = 8,
    ) -> None:
        super().__init__()

        # Context encoder
        self.ctx_encoder = nn.Sequential(
            nn.Linear(self.N_CONTEXT, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
        )

        # Time feature embedding
        self.t_embed = FourierEmbedding(n_freq=n_freq)
        t_dim = self.t_embed.out_dim

        # Main trunk
        in_dim = 64 + t_dim
        layers: list[nn.Module] = []
        prev = in_dim
        for h_dim in hidden_dims:
            layers += [nn.Linear(prev, h_dim), nn.Tanh()]
            prev = h_dim
        layers.append(nn.Linear(prev, 2))  # [h(τ), v(τ)]
        self.trunk = nn.Sequential(*layers)

    def forward(self, tau: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        """
        Parameters
        ----------
        tau     : (B,)         normalised time ∈ [0, 1]
        context : (B, N_CONTEXT)

        Returns
        -------
        (B, 2)  — [h(τ), v(τ)]
        """
        ctx_enc = self.ctx_encoder(context)
        t_enc = self.t_embed(tau)
        x = torch.cat([ctx_enc, t_enc], dim=-1)
        return self.trunk(x)

    def physics_residual(
        self,
        tau: torch.Tensor,
        context: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute ODE residuals  R_h  and  R_v  via automatic differentiation.

        Parameters
        ----------
        tau     : (B,)          normalised time — must allow grad
        context : (B, N_CONTEXT)

        Returns
        -------
        (R_h, R_v)  — residuals; target is all-zeros for a physical trajectory.
        """
        tau = tau.requires_grad_(True)
        out = self.forward(tau, context)
        h = out[:, 0]
        v = out[:, 1]

        # Extract context columns
        Cd = context[:, 2].clamp(min=1e-4)
        A_ref = context[:, 3].clamp(min=1e-6)
        mass = context[:, 4].clamp(min=0.01)
        T_coast = context[:, 5].clamp(min=0.1)

        # Auto-diff derivatives w.r.t. normalised time
        ones = torch.ones_like(h)
        dh_dtau = autograd.grad(h, tau, grad_outputs=ones, create_graph=True, retain_graph=True)[0]
        dv_dtau = autograd.grad(v, tau, grad_outputs=ones, create_graph=True, retain_graph=True)[0]

        # Drag acceleration (sign-preserving)
        rho = isa_density_torch(h)
        drag_accel = 0.5 * rho * v.pow(2) * Cd * A_ref / mass

        # Physics residuals
        R_h = dh_dtau - v * T_coast
        R_v = dv_dtau - (-G - torch.sign(v) * drag_accel) * T_coast

        return R_h, R_v


# ── Multi-term loss ───────────────────────────────────────────────────────────

class PINNLoss(nn.Module):
    """
    Combined training loss with three weighted components:

        L = w_data · MSE(pred, target)
          + w_phys · (‖R_h‖² + ‖R_v‖²)
          + w_ic   · MSE(pred_ic, true_ic)

    Parameters
    ----------
    w_data  : weight for supervised data loss     (default 1.0)
    w_phys  : weight for physics residual loss    (default 0.01)
    w_ic    : weight for initial-condition loss   (default 1.0)

    The physics weight is intentionally small initially; it can be scheduled
    to increase during training (curriculum approach).
    """

    def __init__(
        self,
        w_data: float = 1.0,
        w_phys: float = 0.01,
        w_ic: float = 1.0,
    ) -> None:
        super().__init__()
        self.w_data = w_data
        self.w_phys = w_phys
        self.w_ic = w_ic

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        res_h: torch.Tensor,
        res_v: torch.Tensor,
        ic_pred: torch.Tensor,
        ic_true: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        """
        Compute total loss and all components.

        Returns
        -------
        dict with keys: 'total', 'data', 'physics', 'ic'
        """
        data_loss = nn.functional.huber_loss(pred, target)
        phys_loss = res_h.pow(2).mean() + res_v.pow(2).mean()
        ic_loss = nn.functional.mse_loss(ic_pred, ic_true)
        total = (
            self.w_data * data_loss
            + self.w_phys * phys_loss
            + self.w_ic * ic_loss
        )
        return {
            "total": total,
            "data": data_loss,
            "physics": phys_loss,
            "ic": ic_loss,
        }
