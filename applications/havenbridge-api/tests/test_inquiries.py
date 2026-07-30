"""
Tests for the HavenBridge service-inquiry API routes.

These tests validate:

- Creating a valid inquiry
- Rejecting an invalid email address
- Listing stored inquiries

The real PostgreSQL session is replaced by the FakeDatabaseSession fixture
defined in tests/conftest.py.
"""

from typing import Any

from fastapi.testclient import TestClient


VALID_INQUIRY = {
    "requester_name": "Jordan Demo",
    "requester_email": "jordan.demo@example.org",
    "service_category": "Respite care",
    "message": (
        "I am requesting information about available respite care services."
    ),
}


def test_create_inquiry_returns_created_record(
    client: TestClient,
    fake_db_session: Any,
) -> None:
    """A valid inquiry should be accepted and returned with generated fields."""

    response = client.post(
        "/api/v1/inquiries",
        json=VALID_INQUIRY,
    )

    assert response.status_code == 201

    response_body = response.json()

    assert response_body["id"] == 1
    assert response_body["requester_name"] == "Jordan Demo"
    assert (
        response_body["requester_email"]
        == "jordan.demo@example.org"
    )
    assert response_body["service_category"] == "Respite care"
    assert response_body["status"] == "new"
    assert response_body["created_at"] is not None
    assert response_body["updated_at"] is not None

    # Confirm that the route asked the database session to store one record.
    assert len(fake_db_session.records) == 1


def test_create_inquiry_rejects_invalid_email(
    client: TestClient,
    fake_db_session: Any,
) -> None:
    """Pydantic should reject a malformed requester email address."""

    invalid_inquiry = {
        **VALID_INQUIRY,
        "requester_email": "not-a-valid-email",
    }

    response = client.post(
        "/api/v1/inquiries",
        json=invalid_inquiry,
    )

    assert response.status_code == 422

    validation_errors = response.json()["detail"]

    assert any(
        error["loc"][-1] == "requester_email"
        for error in validation_errors
    )

    # Validation occurs before the inquiry route writes to the database.
    assert fake_db_session.records == []


def test_list_inquiries_returns_stored_records(
    client: TestClient,
) -> None:
    """The GET route should return inquiries created through the POST route."""

    create_response = client.post(
        "/api/v1/inquiries",
        json=VALID_INQUIRY,
    )

    assert create_response.status_code == 201

    list_response = client.get(
        "/api/v1/inquiries",
        params={
            "offset": 0,
            "limit": 10,
        },
    )

    assert list_response.status_code == 200

    response_body = list_response.json()

    assert isinstance(response_body, list)
    assert len(response_body) == 1
    assert response_body[0]["id"] == 1
    assert response_body[0]["requester_name"] == "Jordan Demo"
    assert response_body[0]["status"] == "new"
