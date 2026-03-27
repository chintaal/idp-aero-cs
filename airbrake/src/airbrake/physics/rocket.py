"""
1-D rocket equations of motion.

State vector: [h, v]  — geometric altitude [m], vertical velocity [m/s].

Covers two phases:
  • Powered  (0 ≤ t ≤ burn_time):  thrust + aerodynamic drag + gravity
  • Coast    (t > burn_time):       aerodynamic drag + gravity + airbrake drag
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .atmosphere import density

# Standard gravity
G: float = 9.80665  # [m/s²]


@dataclass
class RocketParams:
    """All physical parameters that describe one rocket configuration."""

    mass_wet: float           # total wet mass at ignition      [kg]
    mass_propellant: float    # propellant mass                 [kg]
    A_ref: float              # reference cross-section area    [m²]
    Cd_body: float            # bare-rocket drag coefficient    (–)
    Cd_brake_max: float       # additional Cd at full deployment (–)
    burn_time: float          # motor burn duration             [s]
    total_impulse: float      # total impulse                   [N·s]
    launch_altitude: float = 0.0  # MSL altitude of launch site [m]

    # ── Derived ──────────────────────────────────────────────────────────────
    @property
    def mass_dry(self) -> float:
        """Dry mass (structure + payload without propellant) [kg]."""
        return self.mass_wet - self.mass_propellant

    @property
    def mean_thrust(self) -> float:
        """Average thrust over burn [N]."""
        return self.total_impulse / self.burn_time

    # ── Methods ──────────────────────────────────────────────────────────────
    def thrust(self, t: float) -> float:
        """Box-car thrust curve (constant thrust during burn)."""
        return self.mean_thrust if 0.0 < t <= self.burn_time else 0.0

    def mass_at(self, t: float) -> float:
        """Linear propellant consumption model."""
        fraction_burned = min(t / self.burn_time, 1.0)
        return self.mass_wet - fraction_burned * self.mass_propellant

    def Cd_at(self, deployment: float) -> float:
        """Total drag coefficient at a given brake deployment fraction [0–1]."""
        return self.Cd_body + self.Cd_brake_max * float(np.clip(deployment, 0.0, 1.0))


def derivatives(
    t: float,
    state: list[float],
    params: RocketParams,
    deployment: float = 0.0,
) -> list[float]:
    """
    Right-hand side of the 1-D equations of motion.

    Parameters
    ----------
    t          : current time [s]
    state      : [h, v]  altitude [m], vertical velocity [m/s]
    params     : rocket physical parameters
    deployment : airbrake deployment fraction [0, 1]

    Returns
    -------
    [dh/dt, dv/dt]
    """
    h, v = state

    # Clamp altitude to launch site to prevent underground integration
    h = max(float(h), params.launch_altitude)

    # Air properties
    rho = density(h)

    # Forces —  positive direction  = upward
    m = params.mass_at(t)
    Cd = params.Cd_at(deployment)

    # Aerodynamic drag magnitude; always opposes velocity
    F_drag = 0.5 * rho * float(v) ** 2 * Cd * params.A_ref
    drag_sign = -np.sign(v) if v != 0.0 else 0.0

    F_thrust = params.thrust(t)
    F_gravity = m * G  # weight force (positive downward)

    # Newton's second law (vertical)
    dv_dt = (F_thrust + drag_sign * F_drag - F_gravity) / m
    dh_dt = float(v)

    return [dh_dt, dv_dt]


def analytical_ballistic_apogee(h0: float, v0: float) -> float:
    """
    Drag-free ballistic apogee estimate (analytical baseline).

    Δh  =  v₀² / (2g)
    h_apogee = h₀ + Δh
    """
    return h0 + max(v0, 0.0) ** 2 / (2.0 * G)
