"""Apogee prediction and deployment decision endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..schemas import (
    ApogeeResponse,
    DeploymentRequest,
    DeploymentResponse,
    FlightState,
)

router = APIRouter()


@router.post(
    "/apogee",
    response_model=ApogeeResponse,
    summary="Predict final apogee from current flight state",
)
async def predict_apogee(state: FlightState, request: Request) -> ApogeeResponse:
    """
    Accept a coast-phase flight state snapshot and return the predicted
    final apogee from the active surrogate model.

    The `rho` field is optional — if omitted the ISA density at the
    supplied altitude is used automatically.
    """
    registry = getattr(request.app.state, "registry", None)
    if registry is None or not registry.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run 'make train-pinn' and restart the server.",
        )

    predicted_apogee = registry.predict_apogee(state)

    return ApogeeResponse(
        predicted_apogee_m=round(predicted_apogee, 2),
        model_used=registry.active_model_name,
        confidence_note=(
            "Surrogate model prediction from coast-phase state. "
            "Accuracy depends on how early in coast the request is made."
        ),
    )


@router.post(
    "/deployment",
    response_model=DeploymentResponse,
    summary="Compute airbrake deployment command",
)
async def compute_deployment(req: DeploymentRequest) -> DeploymentResponse:
    """
    Given a predicted apogee and current flight state, return the
    recommended discrete deployment fraction and a plain-English action.
    """
    from ...control.policy import DeploymentPolicy, FlightPhase

    phase = FlightPhase(req.phase)
    policy = DeploymentPolicy(target_apogee=req.target_apogee_m)
    deployment = policy.compute_deployment(
        predicted_apogee=req.predicted_apogee_m,
        h=req.h,
        v=req.v,
        phase=phase,
    )
    error = req.predicted_apogee_m - req.target_apogee_m

    if deployment == 0.0:
        action = "No deployment — within target or not in coast phase."
    else:
        pct = int(deployment * 100)
        action = f"Deploy brakes to {pct}% — predicted overshoot of {error:.1f} m."

    return DeploymentResponse(
        deployment_fraction=deployment,
        apogee_error_m=round(error, 2),
        phase=phase.value,
        action=action,
    )
