"""
Extended Kalman Filter (EKF) for rocket state estimation.

State  : x = [h, v]  — altitude [m], vertical velocity [m/s]
Inputs : barometric altitude measurement, IMU vertical acceleration

Process model (Euler, dt = integration interval):
    h_{k+1} = h_k + v_k · dt + ½ · a_k · dt²
    v_{k+1} = v_k + a_k · dt

where a_k is the IMU reading (treated as a known control input with noise).

Observation models:
    z_baro  = h  + ε_baro          (barometer)
    z_imu   = v̇  + ε_imu           (IMU residual cross-check)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..physics.atmosphere import density

G: float = 9.80665  # standard gravity [m/s²]


@dataclass
class EKFState:
    """EKF state and covariance at one time step."""

    h: float = 0.0   # estimated altitude      [m]
    v: float = 0.0   # estimated velocity      [m/s]
    P: np.ndarray = field(
        default_factory=lambda: np.diag([25.0, 1.0])  # initial covariance
    )


class RocketEKF:
    """
    Two-state EKF for altitude and vertical velocity estimation.

    Usage
    -----
    ekf = RocketEKF()
    ekf.reset(h0=0.0, v0=0.0)

    # Each control loop iteration:
    ekf.predict(imu_accel, dt)          # propagate with IMU
    ekf.update_baro(h_measured)         # correct with barometer
    # optional physics-based IMU cross-check during coast:
    ekf.update_imu_residual(accel_z, Cd, A_ref, mass)

    altitude = ekf.altitude
    velocity = ekf.velocity
    """

    def __init__(
        self,
        q_h: float = 0.10,    # process noise: altitude  [m²]
        q_v: float = 0.50,    # process noise: velocity  [(m/s)²]
        r_baro: float = 4.0,  # baro noise variance      [m²]
        r_accel: float = 0.09,# accel noise variance     [(m/s²)²]
    ) -> None:
        self.Q = np.diag([q_h, q_v])           # process noise covariance
        self.R_baro = np.array([[r_baro]])      # baro measurement covariance
        self.R_imu = np.array([[r_accel]])      # IMU residual covariance
        self.state = EKFState()

    # ── Initialise ────────────────────────────────────────────────────────────
    def reset(self, h0: float = 0.0, v0: float = 0.0) -> None:
        """Reset filter to a known initial condition."""
        self.state = EKFState(h=h0, v=v0)

    # ── Predict step ──────────────────────────────────────────────────────────
    def predict(self, imu_accel: float, dt: float) -> None:
        """
        Propagate state forward using IMU acceleration as control input.

        Parameters
        ----------
        imu_accel : vertical acceleration from IMU  [m/s²]  (positive up)
        dt        : time step since last call        [s]
        """
        h, v = self.state.h, self.state.v

        # Non-linear state prediction
        h_pred = h + v * dt + 0.5 * imu_accel * dt**2
        v_pred = v + imu_accel * dt

        # Linearised state-transition Jacobian  ∂f/∂x
        F = np.array([[1.0, dt], [0.0, 1.0]])

        # Covariance propagation
        P_pred = F @ self.state.P @ F.T + self.Q

        self.state.h = float(h_pred)
        self.state.v = float(v_pred)
        self.state.P = P_pred

    # ── Update: barometer ─────────────────────────────────────────────────────
    def update_baro(self, h_baro: float) -> None:
        """
        Kalman update from a barometric altitude reading.

        Parameters
        ----------
        h_baro : altitude measured by barometer [m]
        """
        H = np.array([[1.0, 0.0]])  # observation Jacobian  ∂z/∂x
        innovation = h_baro - self.state.h

        S = H @ self.state.P @ H.T + self.R_baro   # innovation covariance
        K = self.state.P @ H.T @ np.linalg.inv(S)  # Kalman gain

        corr = (K @ np.array([[innovation]])).flatten()
        self.state.h += corr[0]
        self.state.v += corr[1]
        self.state.P = (np.eye(2) - K @ H) @ self.state.P

    # ── Update: physics-based IMU cross-check ─────────────────────────────────
    def update_imu_residual(
        self,
        accel_z: float,
        Cd: float,
        A_ref: float,
        mass: float,
    ) -> None:
        """
        Physics-based measurement update using the known coast-phase force balance.

        Expected vertical acceleration during coast:
            a_expected = -g  −  sign(v) · (ρ v² Cd A) / (2 m)

        The difference between the measured IMU value and this prediction
        is treated as an innovation that helps correct the velocity estimate.

        Parameters
        ----------
        accel_z : measured IMU vertical acceleration  [m/s²]
        Cd      : current total drag coefficient
        A_ref   : reference area                       [m²]
        mass    : current rocket mass                  [kg]
        """
        h = max(self.state.h, 0.0)
        v = self.state.v

        rho = density(h)
        drag_accel = 0.5 * rho * v * abs(v) * Cd * A_ref / max(mass, 0.01)
        a_expected = -G - drag_accel  # coast-phase expected acceleration

        innovation = accel_z - a_expected

        # The observation is primarily sensitive to velocity (through drag)
        H = np.array([[0.0, 1.0]])
        S = H @ self.state.P @ H.T + self.R_imu
        K = self.state.P @ H.T @ np.linalg.inv(S)

        corr = (K @ np.array([[innovation]])).flatten()
        self.state.h += corr[0]
        self.state.v += corr[1]
        self.state.P = (np.eye(2) - K @ H) @ self.state.P

    # ── Accessors ─────────────────────────────────────────────────────────────
    @property
    def altitude(self) -> float:
        return self.state.h

    @property
    def velocity(self) -> float:
        return self.state.v

    @property
    def covariance(self) -> np.ndarray:
        return self.state.P.copy()

    @property
    def altitude_std(self) -> float:
        """1-σ altitude uncertainty [m]."""
        return float(np.sqrt(self.state.P[0, 0]))

    @property
    def velocity_std(self) -> float:
        """1-σ velocity uncertainty [m/s]."""
        return float(np.sqrt(self.state.P[1, 1]))
