"""
Trajectory simulation and Monte Carlo dataset generation.

Workflow
--------
1. sample_params()           →  randomise one RocketParams
2. simulate_flight()         →  integrate EOM, return TrajectoryResult
3. generate_dataset()        →  many flights → labelled DataFrame
4. split_by_flight()         →  train / val / test with no leakage
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from .atmosphere import density
from .rocket import RocketParams, derivatives

logger = logging.getLogger(__name__)


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class TrajectoryResult:
    t: np.ndarray          # time points        [s]
    h: np.ndarray          # altitude           [m]
    v: np.ndarray          # vertical velocity  [m/s]
    a: np.ndarray          # vertical accel     [m/s²]
    apogee: float          # peak altitude      [m]
    apogee_time: float     # time of apogee     [s]
    params: RocketParams
    deployment: float


# ── Single flight ─────────────────────────────────────────────────────────────

def simulate_flight(
    params: RocketParams,
    deployment: float = 0.0,
    t_max: float = 150.0,
    dt: float = 0.05,
) -> TrajectoryResult:
    """
    Integrate the rocket equations of motion for one flight.

    Parameters
    ----------
    params     : rocket configuration
    deployment : constant airbrake deployment fraction [0, 1]
    t_max      : maximum integration time [s]
    dt         : output time step [s]

    Returns
    -------
    TrajectoryResult with full time history and computed apogee.
    """
    t_span = (0.0, t_max)
    t_eval = np.arange(0.0, t_max, dt)
    y0 = [params.launch_altitude, 0.0]  # [h₀, v₀]

    # Terminal event: rocket returns to near launch altitude after apogee.
    # Use -0.5 m offset so the event function starts at +0.5 > 0 (not zero),
    # preventing scipy from firing the event immediately at t=0.
    def _ground_event(t, state, p, d):
        return state[0] - (p.launch_altitude - 0.5)

    _ground_event.terminal = True
    _ground_event.direction = -1  # only trigger when descending

    sol = solve_ivp(
        derivatives,
        t_span,
        y0,
        args=(params, deployment),
        t_eval=t_eval,
        events=_ground_event,
        method="RK45",
        max_step=dt,
        rtol=1e-8,
        atol=1e-10,
    )

    if not sol.success:
        raise RuntimeError(f"ODE solver failed: {sol.message}")

    t_arr = sol.t
    h_arr = sol.y[0]
    v_arr = sol.y[1]

    # Compute acceleration via central finite differences
    a_arr = np.gradient(v_arr, t_arr)

    # Apogee = maximum altitude
    apogee_idx = int(np.argmax(h_arr))
    apogee = float(h_arr[apogee_idx])
    apogee_time = float(t_arr[apogee_idx])

    return TrajectoryResult(
        t=t_arr, h=h_arr, v=v_arr, a=a_arr,
        apogee=apogee, apogee_time=apogee_time,
        params=params, deployment=deployment,
    )


# ── Parameter sampler ─────────────────────────────────────────────────────────

def sample_params(rng: np.random.Generator) -> RocketParams:
    """
    Sample one randomised RocketParams for Monte Carlo dataset generation.

    Parameter ranges model typical H–I-class sport/model rockets.
    """
    mass_wet = rng.uniform(0.8, 2.5)
    mass_prop = rng.uniform(0.1, min(0.60, mass_wet * 0.40))  # max 40 % wet mass
    return RocketParams(
        mass_wet=mass_wet,
        mass_propellant=mass_prop,
        A_ref=rng.uniform(0.001, 0.004),      # ~35–70 mm diameter
        Cd_body=rng.uniform(0.40, 0.70),
        Cd_brake_max=rng.uniform(0.40, 1.20),
        burn_time=rng.uniform(1.0, 3.5),
        total_impulse=rng.uniform(50.0, 250.0),  # H-I impulse range [N·s]
        launch_altitude=rng.uniform(0.0, 800.0),
    )


# ── Dataset generation ────────────────────────────────────────────────────────

#: Feature columns produced by generate_dataset()
FEATURE_COLS: list[str] = [
    "h", "v", "a", "deployment", "rho",
    "t_since_burnout", "mass_dry", "A_ref", "Cd_total",
]
TARGET_COL: str = "target_apogee"


def generate_dataset(
    n_flights: int = 2_000,
    samples_per_flight: int = 20,
    noise_std_h: float = 2.0,    # barometer noise [m]
    noise_std_v: float = 0.5,    # derived velocity noise [m/s]
    noise_std_a: float = 0.30,   # IMU noise [m/s²]
    deployments: list[float] | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate a supervised dataset by simulating *n_flights* Monte Carlo flights.

    For each flight several snapshots are taken during the coast phase
    (after burnout, before apogee). Each snapshot is a row:

        [h, v, a, deployment, rho, t_since_burnout, mass_dry, A_ref, Cd_total]
        → target_apogee

    Gaussian sensor noise is injected so the model learns to cope with
    realistic measurement uncertainty.

    Parameters
    ----------
    n_flights          : number of simulated flights
    samples_per_flight : snapshots extracted from each successful flight
    noise_std_h        : 1-σ altitude noise [m]
    noise_std_v        : 1-σ velocity noise [m/s]
    noise_std_a        : 1-σ acceleration noise [m/s²]
    deployments        : list of deployment fractions to use (uniform sample)
    seed               : RNG seed for reproducibility

    Returns
    -------
    pd.DataFrame  with all produced samples plus a 'flight_id' column.
    """
    if deployments is None:
        deployments = [0.0, 0.25, 0.50, 0.75, 1.0]

    rng = np.random.default_rng(seed)
    records: list[dict] = []
    n_failed = 0

    for flight_id in range(n_flights):
        params = sample_params(rng)
        dep = float(rng.choice(deployments))

        try:
            traj = simulate_flight(params, deployment=dep)
        except Exception as exc:
            logger.debug("Flight %d failed: %s", flight_id, exc)
            n_failed += 1
            continue

        # Coast mask: after burnout, before apogee, above ground
        coast_mask = (
            (traj.t > params.burn_time)
            & (traj.t < traj.apogee_time)
            & (traj.h > params.launch_altitude + 1.0)
        )
        coast_indices = np.where(coast_mask)[0]

        if len(coast_indices) < 3:
            n_failed += 1
            continue

        n_samples = min(samples_per_flight, len(coast_indices))
        chosen = rng.choice(coast_indices, size=n_samples, replace=False)

        for idx in chosen:
            h_noisy = float(traj.h[idx]) + rng.normal(0.0, noise_std_h)
            v_noisy = float(traj.v[idx]) + rng.normal(0.0, noise_std_v)
            a_noisy = float(traj.a[idx]) + rng.normal(0.0, noise_std_a)
            t_now = float(traj.t[idx])
            rho = density(max(float(traj.h[idx]), 0.0))

            records.append(
                {
                    # Noisy sensor observations
                    "h": h_noisy,
                    "v": v_noisy,
                    "a": a_noisy,
                    # Known / derived quantities
                    "deployment": dep,
                    "rho": rho,
                    "t_since_burnout": t_now - params.burn_time,
                    "mass_dry": params.mass_dry,
                    "A_ref": params.A_ref,
                    "Cd_total": params.Cd_at(dep),
                    # Target
                    "target_apogee": traj.apogee,
                    # Metadata (kept for splitting, not used as features)
                    "flight_id": flight_id,
                    "total_impulse": params.total_impulse,
                    "launch_altitude": params.launch_altitude,
                }
            )

    df = pd.DataFrame(records)
    logger.info(
        "Dataset: %d samples from %d/%d flights  (%.1f%% failure rate)",
        len(df), n_flights - n_failed, n_flights, 100.0 * n_failed / max(n_flights, 1),
    )
    return df


# ── Train / val / test split by flight ───────────────────────────────────────

def split_by_flight(
    df: pd.DataFrame,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split a dataset into train / validation / test **by flight ID**.

    Splitting by flight ID (not by row) prevents data leakage: all snapshots
    from a given flight belong exclusively to one partition.

    Returns
    -------
    (train_df, val_df, test_df)  — each as a reset-indexed DataFrame.
    """
    rng = np.random.default_rng(seed)
    flight_ids = df["flight_id"].unique().copy()
    rng.shuffle(flight_ids)

    n = len(flight_ids)
    n_train = int(n * train_frac)
    n_val = int(n * val_frac)

    train_ids = set(flight_ids[:n_train])
    val_ids = set(flight_ids[n_train : n_train + n_val])
    test_ids = set(flight_ids[n_train + n_val :])

    logger.info(
        "Split: %d train flights / %d val flights / %d test flights",
        len(train_ids), len(val_ids), len(test_ids),
    )

    return (
        df[df["flight_id"].isin(train_ids)].reset_index(drop=True),
        df[df["flight_id"].isin(val_ids)].reset_index(drop=True),
        df[df["flight_id"].isin(test_ids)].reset_index(drop=True),
    )
