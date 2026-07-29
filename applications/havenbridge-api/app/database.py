"""
PostgreSQL connection management for the HavenBridge API.

This module improves the application by centralizing database-engine creation,
connection pooling, session management, and database-readiness checks.

API routes will request a database session from get_db() instead of creating
unmanaged PostgreSQL connections themselves.
"""

import logging
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """
    Base class for HavenBridge SQLAlchemy database models.

    Future models, such as ServiceInquiry, will inherit from this class so
    SQLAlchemy can map Python classes to PostgreSQL tables.
    """


@lru_cache
def get_engine() -> Engine:
    """
    Create and cache the SQLAlchemy PostgreSQL engine.

    The engine manages the connection pool shared by the API process.
    It is created lazily so importing this module does not immediately require
    PostgreSQL to be available. This also makes local testing easier.
    """

    settings = get_settings()

    # URL.create safely handles special characters in database credentials.
    # The psycopg driver is selected explicitly rather than relying on defaults.
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.get_postgres_password(),
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
    )

    return create_engine(
        database_url,

        # Check a pooled connection before giving it to an API request.
        # This helps recover cleanly from stale or interrupted connections.
        pool_pre_ping=True,

        # Keep a controlled number of reusable database connections.
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,

        # PostgreSQL driver-level connection settings.
        connect_args={
            "connect_timeout": settings.db_connect_timeout_seconds,
            "application_name": "havenbridge-api",
        },
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """
    Create and cache the database-session factory.

    Each API request receives its own SQLAlchemy Session while sharing the
    application-wide connection pool.
    """

    return sessionmaker(
        bind=get_engine(),
        class_=Session,

        # Changes are sent deliberately through commit or flush operations.
        autoflush=False,

        # Keep loaded values available after a successful commit.
        expire_on_commit=False,
    )


def get_db() -> Generator[Session, None, None]:
    """
    Provide one managed database session to an API request.

    FastAPI will call this function as a dependency. The session is always
    closed, and failed operations are rolled back before the error continues.
    """

    session = get_session_factory()()

    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def database_is_ready() -> bool:
    """
    Confirm that the API can execute a query against PostgreSQL.

    The future /health/ready endpoint will use this function. A successful
    SELECT 1 proves more than process health: it confirms that the API can
    acquire a connection and communicate with the database.
    """

    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except SQLAlchemyError as exc:
        # Log the database failure without logging credentials.
        logger.warning(
            "PostgreSQL readiness check failed: %s",
            exc,
        )

        return False
