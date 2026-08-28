#What it does: verifies that /metrics works, returns Prometheus-formatted data,
#exposes our HavenBridge metrics, records normal application requests,
#and does not count Prometheus's own /metrics scrapes as application traffic.


"""
Tests for HavenBridge Prometheus application metrics.

These tests verify that:

- The /metrics endpoint is available.
- Prometheus-formatted metrics are returned.
- HavenBridge HTTP request metrics are exposed.
- Normal application requests are recorded.
- Prometheus scrapes are not counted as application traffic.

The tests use the shared FastAPI TestClient fixture and therefore do not
require PostgreSQL, Kubernetes, or a running Uvicorn process.
"""

from fastapi.testclient import TestClient


def test_metrics_endpoint_returns_prometheus_metrics(
    client: TestClient,
) -> None:
    """The metrics endpoint should return Prometheus-formatted output."""

    response = client.get("/metrics")

    assert response.status_code == 200

    assert "text/plain" in response.headers["content-type"]

    assert "havenbridge_http_requests_total" in response.text

    assert (
        "havenbridge_http_request_duration_seconds"
        in response.text
    )


def test_application_request_is_recorded_in_metrics(
    client: TestClient,
) -> None:
    """A normal API request should appear in HavenBridge HTTP metrics."""

    application_response = client.get("/health/live")

    assert application_response.status_code == 200

    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200

    assert 'method="GET"' in metrics_response.text
    assert 'route="/health/live"' in metrics_response.text
    assert 'status_code="200"' in metrics_response.text


def test_metrics_endpoint_is_not_counted_as_application_traffic(
    client: TestClient,
) -> None:
    """
    Prometheus scraping /metrics should not inflate application traffic.

    The /metrics endpoint is intentionally excluded from the HavenBridge
    HTTP request counter and request-duration histogram.
    """

    response = client.get("/metrics")

    assert response.status_code == 200

    assert 'route="/metrics"' not in response.text
