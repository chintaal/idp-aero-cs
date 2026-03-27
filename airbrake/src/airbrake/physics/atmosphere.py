"""
International Standard Atmosphere (ISA) model — troposphere + lower stratosphere.

Reference: ICAO Doc 7488/3, 1993.
"""
from __future__ import annotations

import numpy as np

# ── ISA physical constants ────────────────────────────────────────────────────
T0: float = 288.15      # sea-level temperature         [K]
P0: float = 101_325.0   # sea-level pressure             [Pa]
RHO0: float = 1.225     # sea-level density              [kg/m³]
L: float = 0.0065       # tropospheric lapse rate        [K/m]
R_AIR: float = 287.058  # specific gas constant for air  [J/(kg·K)]
G0: float = 9.80665     # standard gravity               [m/s²]
H_TROP: float = 11_000.0  # tropopause altitude           [m]
T_TROP: float = 216.65  # isothermal stratosphere temp   [K]
P_TROP: float = 22_632.1  # pressure at tropopause       [Pa]

# Derived exponent used in pressure formula
_EXP: float = G0 / (L * R_AIR)  # ≈ 5.2561


def temperature(h: float) -> float:
    """ISA temperature at geometric altitude *h* [m], returns [K]."""
    return T0 - L * h if h < H_TROP else T_TROP


def pressure(h: float) -> float:
    """ISA static pressure at altitude *h* [m], returns [Pa]."""
    if h < H_TROP:
        return P0 * (temperature(h) / T0) ** _EXP
    return P_TROP * np.exp(-G0 * (h - H_TROP) / (R_AIR * T_TROP))


def density(h: float) -> float:
    """ISA air density at altitude *h* [m], returns [kg/m³]."""
    return pressure(h) / (R_AIR * temperature(h))


# ── Vectorised versions (NumPy arrays) ───────────────────────────────────────

def temperature_vec(h: np.ndarray) -> np.ndarray:
    """Vectorised ISA temperature."""
    h = np.asarray(h, dtype=np.float64)
    return np.where(h < H_TROP, T0 - L * h, T_TROP)


def pressure_vec(h: np.ndarray) -> np.ndarray:
    """Vectorised ISA pressure."""
    h = np.asarray(h, dtype=np.float64)
    T = temperature_vec(h)
    return np.where(
        h < H_TROP,
        P0 * (T / T0) ** _EXP,
        P_TROP * np.exp(-G0 * np.maximum(h - H_TROP, 0.0) / (R_AIR * T_TROP)),
    )


def density_vec(h: np.ndarray) -> np.ndarray:
    """Vectorised ISA density."""
    h = np.asarray(h, dtype=np.float64)
    return pressure_vec(h) / (R_AIR * temperature_vec(h))


def speed_of_sound(h: float) -> float:
    """Speed of sound at altitude *h* [m], returns [m/s]."""
    gamma = 1.4
    return float(np.sqrt(gamma * R_AIR * temperature(h)))
