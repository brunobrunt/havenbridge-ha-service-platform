"""
Prometheus metrics for the HavenBridge API.

This module defines application-level HTTP metrics and registers the
instrumentation required for Prometheus to scrape the FastAPI application.

Keeping observability code separate from main.py prevents the application
entry point from becoming overloaded as HavenBridge grows.
"""

from time import perf_counter

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)


HTTP_REQUESTS_TOTAL = Counter(
    "havenbridge_http_requests_total",
    "Total number of HTTP requests handled by the HavenBridge API.",
    ["method", "route", "status_code"],
)


HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "havenbridge_http_request_duration_seconds",
    "Time spent handling HavenBridge API HTTP requests.",
    ["method", "route"],
)


def configure_metrics(app: FastAPI) -> None:
    """
    Register Prometheus HTTP instrumentation with the FastAPI application.

    The middleware records request counts and request duration.

    Route templates are used instead of raw request URLs so identifiers such
    as individual inquiry IDs do not create unbounded Prometheus label values.
    """

    @app.middleware("http")
    async def record_http_metrics(
        request: Request,
        call_next,
    ) -> Response:
        """
        Record request count, status code, route, and request duration.
        """

        start_time = perf_counter()

        response = await call_next(request)

        duration = perf_counter() - start_time

        route_object = request.scope.get("route")
        route = getattr(
            route_object,
            "path",
            "unmatched",
        )

        # Avoid recording Prometheus scraping itself as application traffic.
        if route != "/metrics":
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                route=route,
                status_code=str(response.status_code),
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                route=route,
            ).observe(duration)

        return response

    @app.get(
        "/metrics",
        include_in_schema=False,
    )
    def metrics() -> Response:
        """
        Expose Prometheus-formatted HavenBridge application metrics.
        """

        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )
