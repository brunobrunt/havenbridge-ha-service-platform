"""
Tests for the HavenBridge liveness and readiness endpoints.

Liveness confirms that the FastAPI process can respond.

Readiness confirms whether the API considers its PostgreSQL dependency
available. The database check is replaced with predictable test values so
these tests do not need the Kubernetes PostgreSQL service.
"""

import pytest
from fastapi.testclient import TestClient

import app.routers.health as health_router_module


def test_liveness_endpoint_returns_healthy(
    client: TestClient,
) -> None:
    """The liveness endpoint should report a healthy API process."""

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
    }


def test_readiness_endpoint_returns_ready_when_database_available(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Readiness should succeed when the database check succeeds."""

    monkeypatch.setattr(
        health_router_module,
        "database_is_ready",
        lambda: True,
    )

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
    }


def test_readiness_endpoint_returns_503_when_database_unavailable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Readiness should fail when PostgreSQL is unavailable."""

    monkeypatch.setattr(
        health_router_module,
        "database_is_ready",
        lambda: False,
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert "detail" in response.json()
