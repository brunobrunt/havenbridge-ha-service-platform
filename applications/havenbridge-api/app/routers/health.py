"""
Health endpoints for the HavenBridge API.

This router improves the application by exposing separate liveness and
readiness checks for Kubernetes.

Liveness answers:
    Is the FastAPI process running?

Readiness answers:
    Can the FastAPI process communicate with PostgreSQL?

Keeping these checks separate prevents Kubernetes from sending application
traffic to a Pod that is running but cannot access its required database.
"""

from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.database import database_is_ready


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


class HealthResponse(BaseModel):
    """
    Standard response returned by HavenBridge health endpoints.

    A response model keeps the health-check output predictable for Kubernetes,
    operators, monitoring systems, and automated tests.
    """

    status: Literal["healthy", "ready"]


@router.get(
    "/live",
    response_model=HealthResponse,
    summary="Check API process health",
)
def liveness_check() -> HealthResponse:
    """
    Confirm that the HavenBridge API process is running.

    This endpoint deliberately does not query PostgreSQL. A temporary database
    outage should not cause Kubernetes to repeatedly restart a healthy API
    process.
    """

    return HealthResponse(status="healthy")


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Check API and database readiness",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "PostgreSQL is unavailable.",
        },
    },
)
def readiness_check() -> HealthResponse:
    """
    Confirm that the API can execute a query against PostgreSQL.

    Kubernetes will use this endpoint to decide whether the Pod is ready to
    receive application traffic.
    """

    if not database_is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL is unavailable.",
        )

    return HealthResponse(status="ready")
