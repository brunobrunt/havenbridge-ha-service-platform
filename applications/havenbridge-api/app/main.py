"""
Main entry point for the HavenBridge API.

This module creates the FastAPI application, configures application lifecycle
handling, and registers the endpoint routers.

Keeping the application entry point small makes the backend easier to test,
maintain, containerize, and extend with additional HavenBridge features.
"""
import os
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Response

# Importing models registers SQLAlchemy table definitions with Base.metadata.
# Without this import, create_all() would not know about service_inquiries.
from app import models  # noqa: F401

from app.config import get_settings
from app.database import Base, get_engine
from app.metrics import configure_metrics

# Import the health and service-inquiry routers
from app.routers import health, inquiries


settings = get_settings()


def configure_logging() -> None:
    """
    Configure consistent logging for the HavenBridge API.

    Kubernetes collects container standard output, so application logs are
    written to the console instead of local log files inside the container.
    """

    log_level = getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    )

    logging.basicConfig(
        level=log_level,
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s "
            "%(message)s"
        ),
    )


configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manage application startup and shutdown activities.

    Startup records that the API process has begun. It does not require
    PostgreSQL to be immediately available because the readiness endpoint is
    responsible for controlling whether the Pod receives traffic.

    Shutdown disposes of the SQLAlchemy connection pool only when the engine
    was created during the application's lifetime.
    """

    logger.info(
    "Starting %s in %s mode.",
     settings.app_name,
     settings.app_environment,
    )

    if settings.db_auto_create_tables:
        logger.info(
            "Creating missing HavenBridge database tables."
        )

        # Create tables registered through SQLAlchemy models.
        #
        # create_all() creates missing tables but does not delete existing
        # tables or remove existing PostgreSQL data.
        Base.metadata.create_all(
            bind=get_engine(),
        )

    yield

    # Avoid creating a new database engine during shutdown when the API never
    # used PostgreSQL during its lifetime.
    if get_engine.cache_info().currsize > 0:
        logger.info("Closing PostgreSQL connection pool.")
        get_engine().dispose()

    logger.info("HavenBridge API shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for HavenBridge service inquiries and referrals."
    ),
    lifespan=lifespan,
)

ENABLE_OBSERVABILITY_TEST_ENDPOINTS = (
    os.getenv("ENABLE_OBSERVABILITY_TEST_ENDPOINTS", "false").lower() == "true"
)

# Register Prometheus application metrics.
#
# This adds HTTP request instrumentation and exposes the /metrics endpoint
# that Prometheus will scrape inside Kubernetes.
configure_metrics(app)


# Register health endpoints with the main FastAPI application.
#
# Additional routers, such as service inquiries, will be registered here as
# the backend is developed.

# Register Kubernetes liveness and readiness endpoints.

# Register service-inquiry API endpoints.


# Attach the health router to the main FastAPI application.
# This makes /health/live and /health/ready available to clients.
app.include_router(health.router)

# Attach the inquiry router to the main FastAPI application.
# inquiries.py defines the routes, while include_router() exposes them
# through the running HavenBridge API.
app.include_router(inquiries.router)


@app.get(
    "/",
    tags=["Application"],
    summary="Show basic API information",
)
def root() -> dict[str, str]:
    """
    Return basic information about the HavenBridge API.

    This endpoint gives developers and operators a simple confirmation that
    they reached the expected application.
    """

    return {
        "name": settings.app_name,
        "environment": settings.app_environment,
        "version": settings.app_version,
        "documentation": "/docs",
        "liveness": "/health/live",
        "readiness": "/health/ready",
    }


# CI change-detection positive validation marker.
# Controlled endpoint used for observability and alerting validation.
# Disabled by default unless ENABLE_OBSERVABILITY_TEST_ENDPOINTS=true.
if ENABLE_OBSERVABILITY_TEST_ENDPOINTS:

    @app.get("/test/500", include_in_schema=False)
    def test_server_error() -> Response:
        """
        Return an intentional HTTP 500 response for controlled
        observability and alerting validation.
        """
        return Response(status_code=500)
