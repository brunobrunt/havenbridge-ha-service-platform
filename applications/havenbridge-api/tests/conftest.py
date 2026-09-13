"""
Shared Pytest fixtures for the HavenBridge API test suite.

These fixtures replace the real PostgreSQL database session with a controlled
in-memory substitute.

This allows unit-style API tests to run without:

- Starting the PostgreSQL SSH tunnel
- Connecting to the Kubernetes cluster
- Starting Uvicorn
- Creating or modifying real PostgreSQL tables
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
from app.models import InquiryStatusHistory, ServiceInquiry


class FakeScalarResult:
    """
    Represent a simplified SQLAlchemy query result.

    The HavenBridge routes may use either:

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

        The fake records are already model objects, so no conversion
        is required.
        """

        return self

    def all(self) -> list[Any]:
        """Return a copy of all records currently stored in the fake result."""

        return list(self._records)


class FakeDatabaseSession:
    """
    Provide the SQLAlchemy Session behaviour used by HavenBridge routes.

    The fake database keeps service inquiries and inquiry status history
    separate, similar to the two PostgreSQL tables used by the application.

    It implements only the Session operations currently required by the
    HavenBridge API tests.
    """

    def __init__(self) -> None:
        """Create a new empty fake database session for a test."""

        # Simulates the service_inquiries table.
        self.records: list[ServiceInquiry] = []

        # Simulates the inquiry_status_history table.
        self.history_records: list[InquiryStatusHistory] = []

        self.rollback_called = False

        self._pending_record: Any | None = None
        self._selected_record: ServiceInquiry | None = None

        # The two PostgreSQL tables have independent primary-key sequences.
        self._next_inquiry_id = 1
        self._next_history_id = 1

    def add(self, record: Any) -> None:
        """
        Hold a new model object until commit() is called.

        The pending object may now be either:

        - ServiceInquiry
        - InquiryStatusHistory
        """

        self._pending_record = record

    def commit(self) -> None:
        """
        Simulate committing the current transaction.

        ServiceInquiry inserts receive:

        - Primary-key ID
        - Default status
        - created_at
        - updated_at

        InquiryStatusHistory inserts receive:

        - Primary-key ID
        - changed_at

        When a previously selected inquiry is being updated, its updated_at
        timestamp is also refreshed.
        """

        current_time = datetime.now(timezone.utc)

        # A selected inquiry represents an existing database row being changed.
        if self._selected_record is not None:
            self._selected_record.updated_at = current_time

        # Nothing new was added to the transaction.
        if self._pending_record is None:
            self._selected_record = None
            return

        if isinstance(self._pending_record, ServiceInquiry):
            inquiry = self._pending_record

            inquiry.id = self._next_inquiry_id

            if not inquiry.status:
                inquiry.status = "new"

            inquiry.created_at = current_time
            inquiry.updated_at = current_time

            self.records.append(inquiry)

            self._next_inquiry_id += 1

        elif isinstance(self._pending_record, InquiryStatusHistory):
            history = self._pending_record

            history.id = self._next_history_id
            history.changed_at = current_time

            self.history_records.append(history)

            self._next_history_id += 1

        else:
            raise TypeError(
                "FakeDatabaseSession received an unsupported model type: "
                f"{type(self._pending_record).__name__}"
            )

        self._pending_record = None
        self._selected_record = None

    def refresh(self, record: Any) -> None:
        """
        Simulate refreshing a model from PostgreSQL.

        The fake commit() method already assigns generated values, so no
        additional work is required here.
        """

    def rollback(self) -> None:
        """
        Simulate rolling back a failed transaction.

        Pending changes are discarded and the rollback flag is recorded.
        """

        self.rollback_called = True
        self._pending_record = None
        self._selected_record = None

    def get(
        self,
        model: Any,
        record_id: int,
    ) -> Any | None:
        """
        Return one stored record by primary-key ID.

        This simulates SQLAlchemy Session.get().
        """

        if model is ServiceInquiry:
            for record in self.records:
                if record.id == record_id:
                    self._selected_record = record
                    return record

            return None

        if model is InquiryStatusHistory:
            for record in self.history_records:
                if record.id == record_id:
                    return record

            return None

        return None

    def scalars(self, statement: Any) -> FakeScalarResult:
        """
        Return stored model objects for a SQLAlchemy SELECT statement.

        The fake session checks which model the statement is selecting when
        possible. ServiceInquiry remains the default because the existing
        inquiry-list endpoint selects that model.
        """

        try:
            descriptions = statement.column_descriptions

            if descriptions:
                entity = descriptions[0].get("entity")

                if entity is InquiryStatusHistory:
                    return FakeScalarResult(self.history_records)

        except (AttributeError, IndexError, TypeError):
            pass

        return FakeScalarResult(self.records)

    def execute(self, statement: Any) -> FakeScalarResult:
        """
        Support routes that use execute().scalars().all().
        """

        return self.scalars(statement)


@pytest.fixture
def fake_db_session() -> FakeDatabaseSession:
    """
    Give each test a separate empty fake database session.

    Pytest creates a fresh instance for every test function so records from
    one test cannot leak into another test.
    """

    return FakeDatabaseSession()


@pytest.fixture
def client(
    fake_db_session: FakeDatabaseSession,
) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI TestClient using the fake database session.

    The production get_db() dependency is replaced for the duration of
    each test, so the unit tests do not write to HavenBridge PostgreSQL.
    """

    def override_get_db() -> Generator[
        FakeDatabaseSession,
        None,
        None,
    ]:
        """Provide the fake database session to HavenBridge API routes."""

        yield fake_db_session

    main_module.app.dependency_overrides[get_db] = override_get_db

    # Avoid running the application lifespan in these unit-style tests.
    test_client = TestClient(main_module.app)

    try:
        yield test_client

    finally:
        test_client.close()
        main_module.app.dependency_overrides.clear()
