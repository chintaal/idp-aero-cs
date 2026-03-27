"""
Pydantic schemas for the Airbrake Apogee Prediction API.

All schemas use strict Pydantic v2 validators with meaningful bounds
derived from the flight envelope defined in the system requirements.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Prediction schemas ────────────────────────────────────────────────────────

class FlightState(BaseModel):
    """
    Current in-flight state snapshot for real-time apogee prediction.

    All values are in SI units relative to the launch site.
    """

    h: float = Field(
        ...,
        description="Altitude above launch site [m]",
        ge=0.0,
        le=15_000.0,
    )
    v: float = Field(
        ...,
        description="Vertical velocity, positive upward [m/s]",
        ge=-500.0,
        le=1_000.0,
    )
    deployment: float = Field(
        default=0.0,
        description="Current airbrake deployment fraction [0–1]",
        ge=0.0,
        le=1.0,
    )
    rho: Optional[float] = Field(
        default=None,
        description="Air density [kg/m³]. Auto-computed from altitude if omitted.",
        gt=0.0,
        le=1.5,
    )
    t_since_burnout: float = Field(
        ...,
        description="Seconds since motor burnout [s]",
        ge=0.0,
        le=300.0,
    )
    mass_dry: float = Field(
        default=1.2,
        description="Rocket dry mass [kg]",
        gt=0.0,
        le=10.0,
    )
    A_ref: float = Field(
        default=0.002,
        description="Reference cross-section area [m²]",
        gt=0.0,
        le=0.1,
    )
    Cd_total: float = Field(
        default=0.55,
        description="Total drag coefficient including brake contribution",
        gt=0.0,
        le=5.0,
    )

    @model_validator(mode="after")
    def _fill_density(self) -> "FlightState":
        """Auto-compute ISA density if not provided."""
        if self.rho is None:
            from ..physics.atmosphere import density
            self.rho = density(max(self.h, 0.0))
        return self


class ApogeeResponse(BaseModel):
    predicted_apogee_m: float = Field(..., description="Predicted final apogee [m]")
    model_used: str = Field(..., description="Name of the active inference model")
    confidence_note: str = Field(..., description="Human-readable quality note")


# ── Deployment decision schemas ───────────────────────────────────────────────

class DeploymentRequest(BaseModel):
    predicted_apogee_m: float = Field(..., description="Predicted apogee from /predict/apogee [m]")
    target_apogee_m: float = Field(default=300.0, gt=0.0, description="Mission target altitude [m]")
    h: float = Field(..., ge=0.0, description="Current altitude [m]")
    v: float = Field(..., description="Current vertical velocity [m/s]")
    phase: str = Field(default="coast", description="Flight phase: ground|powered|coast|near_apogee|descent")

    @field_validator("phase")
    @classmethod
    def _valid_phase(cls, v: str) -> str:
        valid = {"ground", "powered", "coast", "near_apogee", "descent"}
        if v not in valid:
            raise ValueError(f"phase must be one of {sorted(valid)}")
        return v


class DeploymentResponse(BaseModel):
    deployment_fraction: float = Field(..., ge=0.0, le=1.0)
    apogee_error_m: float = Field(..., description="Predicted − target [m]; positive = overshoot")
    phase: str
    action: str = Field(..., description="Human-readable action description")


# ── Simulation schemas ────────────────────────────────────────────────────────

class SimulationRequest(BaseModel):
    """Parameters for an on-demand single-flight simulation."""

    mass_wet: float = Field(default=1.5, gt=0.0, le=20.0, description="Wet mass [kg]")
    mass_propellant: float = Field(default=0.3, gt=0.0, le=5.0, description="Propellant mass [kg]")
    A_ref: float = Field(default=0.002, gt=0.0, le=0.1, description="Reference area [m²]")
    Cd_body: float = Field(default=0.55, gt=0.0, le=3.0, description="Body drag coefficient")
    Cd_brake_max: float = Field(default=0.80, gt=0.0, le=3.0, description="Max additional Cd from brakes")
    burn_time: float = Field(default=2.0, gt=0.0, le=30.0, description="Motor burn duration [s]")
    total_impulse: float = Field(default=100.0, gt=0.0, le=10_000.0, description="Total impulse [N·s]")
    deployment: float = Field(default=0.0, ge=0.0, le=1.0, description="Fixed deployment fraction")
    launch_altitude: float = Field(default=0.0, ge=0.0, le=5_000.0, description="Site altitude MSL [m]")

    @model_validator(mode="after")
    def _propellant_less_than_wet(self) -> "SimulationRequest":
        if self.mass_propellant >= self.mass_wet:
            raise ValueError("mass_propellant must be less than mass_wet")
        return self


class SimulationResponse(BaseModel):
    apogee_m: float
    apogee_time_s: float
    trajectory_points: int
    burn_time_s: float
    mean_thrust_n: float


# ── Health schema ─────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    active_model: str
    version: str = "1.0.0"
