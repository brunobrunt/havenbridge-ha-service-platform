"""
Shared Pytest fixtures for the HavenBridge API test suite.

These fixtures replace the real PostgreSQL database session with a controlled
in-memory substitute.

This allows unit-style API tests to run without:

- Starting the PostgreSQL SSH tunnel
- Connecting to the Kubernetes cluster
- Starting Uvicorn
- Creating real PostgreSQL tables
- Writing test data to the HavenBridge database

Real PostgreSQL integration tests will be implemented separately.
"""

from collections.abc import Generator
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.database import get_db


class FakeScalarResult:
    """
    Represent a simplified SQLAlchemy query result.

    The HavenBridge inquiry-listing route may use either:

        db.scalars(statement).all()

    or:

        db.execute(statement).scalars().all()

    This fake result supports both patterns without connecting to PostgreSQL.
    """

    def __init__(self, records: list[Any]) -> None:
        """Store the records that will be returned by the fake query."""

        self._records = records

    def scalars(self) -> "FakeScalarResult":
        """
        Return this object to support execute().scalars().all().

        A real SQLAlchemy result converts database rows into scalar model
        objects. The fake records are already model objects, so no conversion
        is required.
        """

        return self

    def all(self) -> list[Any]:
        """Return a copy of all records currently stored in the fake session."""

        return list(self._records)


class FakeDatabaseSession:
    """
    Provide the SQLAlchemy Session behaviour used by HavenBridge routes.

    This class is intentionally small. It does not attempt to reproduce all
    SQLAlchemy or PostgreSQL features.

    It only implements the methods currently used by the inquiry routes:

    - add()
    - commit()
    - refresh()
    - rollback()
    - scalars()
    - execute()
    """

    def __init__(self) -> None:
        """Create a new empty fake database session for a test."""

        self.records: list[Any] = []
        self.rollback_called = False

        self._pending_record: Any | None = None
        self._selected_record: Any | None = None
        self._next_id = 1

    def add(self, record: Any) -> None:
        """
        Hold a new model until commit() is called.

        A real SQLAlchemy session tracks the object as part of a transaction.
        The fake session stores it temporarily as the pending record.
        """

        self._pending_record = record

    def commit(self) -> None:
        """
        Simulate PostgreSQL committing a newly created inquiry.

        PostgreSQL normally generates values such as:

        - Primary-key ID
        - Default status
        - Creation timestamp
        - Update timestamp

        The fake session assigns those values so FastAPI can serialize the
        response exactly as it would after a real database insert.
        """

        current_time = datetime.now(timezone.utc)

        if self._pending_record is None:
            if self._selected_record is not None:
                self._selected_record.updated_at = current_time
                self._selected_record = None

            return

        self._pending_record.id = self._next_id

        if not self._pending_record.status:
            self._pending_record.status = "new"

        self._pending_record.created_at = current_time
        self._pending_record.updated_at = current_time

        self.records.append(self._pending_record)

        self._next_id += 1
        self._pending_record = None

    def refresh(self, record: Any) -> None:
        """
        Simulate refreshing a model from PostgreSQL.

        In the real application, SQLAlchemy refreshes the object after commit
        so generated database values become available.

        The fake commit() method already adds those values, so this method does
        not need to perform another action.
        """

    def rollback(self) -> None:
        """
        Simulate rolling back a failed transaction.

        The flag allows future tests to verify that rollback() was requested
        when an exception occurred.
        """

        self.rollback_called = True
        self._pending_record = None

    def get(
        self,
        model: Any,
        record_id: int,
    ) -> Any | None:
        """
        Return one stored record by primary-key ID.

        This simulates SQLAlchemy Session.get().
        """

        for record in self.records:
            if record.id == record_id:
                self._selected_record = record
                return record

        return None

    def scalars(self, statement: Any) -> FakeScalarResult:
        """
        Return stored inquiries for a SQLAlchemy select statement.

        The statement argument is accepted to match SQLAlchemy's interface,
        but the fake database does not parse or execute SQL.
        """

        return FakeScalarResult(self.records)

    def execute(self, statement: Any) -> FakeScalarResult:
        """
        Support routes that use execute().scalars().all().

        The statement argument is accepted for compatibility with SQLAlchemy.
        """

        return FakeScalarResult(self.records)


@pytest.fixture
def fake_db_session() -> FakeDatabaseSession:
    """
    Give each test a separate empty fake database session.

    Pytest creates a fresh instance for every test function. This prevents
    records created in one test from leaking into another test.
    """

    return FakeDatabaseSession()


@pytest.fixture
def client(
    fake_db_session: FakeDatabaseSession,
) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI TestClient without running application startup.

    The real PostgreSQL dependency is replaced with FakeDatabaseSession.

    TestClient is deliberately not used as a context manager here. Using:

        with TestClient(app) as client:

    would run the FastAPI lifespan function. The HavenBridge lifespan currently
    runs Base.metadata.create_all(), which would attempt to connect to the real
    PostgreSQL database through 127.0.0.1:15432.

    Creating TestClient normally, without the context-manager form, allows
    these unit tests to run without the SSH tunnel or Kubernetes PostgreSQL.
    """

    def override_get_db() -> Generator[
        FakeDatabaseSession,
        None,
        None,
    ]:
        """
        Provide the fake database session to HavenBridge API routes.

        FastAPI uses this function instead of the production get_db()
        dependency for the duration of the test.
        """

        yield fake_db_session

    # Replace the production SQLAlchemy database dependency.
    main_module.app.dependency_overrides[get_db] = override_get_db

    # Do not use TestClient as a context manager in these unit tests.
    # The context-manager form would run the FastAPI lifespan and attempt
    # PostgreSQL table creation.
    test_client = TestClient(main_module.app)

    try:
        yield test_client
    finally:
        # Close the underlying HTTP client after the test completes.
        test_client.close()

        # Remove all dependency overrides so one test cannot affect another.
        main_module.app.dependency_overrides.clear()
