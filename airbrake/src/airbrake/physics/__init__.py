"""Physics sub-package: ISA atmosphere, rocket EOM, trajectory simulation."""

from .atmosphere import density, density_vec, pressure, temperature
from .rocket import RocketParams, analytical_ballistic_apogee, derivatives
from .simulation import (
    TrajectoryResult,
    FEATURE_COLS,
    TARGET_COL,
    generate_dataset,
    simulate_flight,
    split_by_flight,
)

__all__ = [
    "density", "density_vec", "pressure", "temperature",
    "RocketParams", "analytical_ballistic_apogee", "derivatives",
    "TrajectoryResult", "FEATURE_COLS", "TARGET_COL",
    "generate_dataset", "simulate_flight", "split_by_flight",
]
