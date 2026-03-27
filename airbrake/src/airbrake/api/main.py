"""
FastAPI application factory and entry point.

Architecture
------------
  GET  /health/        — liveness + model status
  POST /predict/apogee — surrogate apogee prediction
  POST /predict/deployment — deployment command
  POST /simulate/trajectory — on-demand physics simulation

The registry (ModelRegistry) is loaded once at startup via the lifespan
context manager and stored on app.state so it is available to all routes
without importing globals.

Running
-------
  uvicorn airbrake.api.main:app --host 0.0.0.0 --port 8000 --reload
  # or
  make serve
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, predict, simulate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Load the model registry on startup; clean up on shutdown."""
    from ..models.registry import ModelRegistry

    artifacts_dir = Path(os.getenv("ARTIFACTS_DIR", "artifacts"))
    registry = ModelRegistry(artifacts_dir=artifacts_dir)
    registry.load_default()
    application.state.registry = registry

    if registry.is_loaded:
        logger.info("Registry ready — active model: %s", registry.active_model_name)
    else:
        logger.warning(
            "No model loaded. Prediction endpoints will return 503 until a model is trained."
        )

    yield
    logger.info("API shutting down.")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    app = FastAPI(
        title="Airbrake Apogee Prediction API",
        description=(
            "Physics-simulation-driven, PINN-backed real-time apogee prediction "
            "and airbrake deployment control for model rocket flights.\n\n"
            "**Quick start**: `POST /simulate/trajectory` to verify the physics, "
            "then `POST /predict/apogee` + `POST /predict/deployment` for the "
            "full closed-loop control loop."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(predict.router, prefix="/predict", tags=["Prediction"])
    app.include_router(simulate.router, prefix="/simulate", tags=["Simulation"])

    return app


app = create_app()
