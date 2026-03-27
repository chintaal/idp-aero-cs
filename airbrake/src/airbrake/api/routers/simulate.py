"""On-demand trajectory simulation endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from ..schemas import SimulationRequest, SimulationResponse

router = APIRouter()


@router.post(
    "/trajectory",
    response_model=SimulationResponse,
    summary="Simulate a single rocket flight",
)
async def run_trajectory(req: SimulationRequest) -> SimulationResponse:
    """
    Integrate the 1-D equations of motion for the supplied rocket parameters
    and return the apogee and trajectory summary.

    This endpoint is intentionally **synchronous / blocking** in the current
    form.  For long simulations on a production server, wrap in a background
    task or move to a worker queue.
    """
    from ...physics.rocket import RocketParams
    from ...physics.simulation import simulate_flight

    params = RocketParams(
        mass_wet=req.mass_wet,
        mass_propellant=req.mass_propellant,
        A_ref=req.A_ref,
        Cd_body=req.Cd_body,
        Cd_brake_max=req.Cd_brake_max,
        burn_time=req.burn_time,
        total_impulse=req.total_impulse,
        launch_altitude=req.launch_altitude,
    )

    traj = simulate_flight(params, deployment=req.deployment)

    return SimulationResponse(
        apogee_m=round(traj.apogee, 2),
        apogee_time_s=round(traj.apogee_time, 3),
        trajectory_points=len(traj.t),
        burn_time_s=params.burn_time,
        mean_thrust_n=round(params.mean_thrust, 1),
    )
