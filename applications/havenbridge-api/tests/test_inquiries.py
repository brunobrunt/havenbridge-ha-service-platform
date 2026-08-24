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


def test_get_inquiry_returns_requested_record(
    client: TestClient,
) -> None:
    """An existing inquiry should be retrievable by its ID."""

    create_response = client.post(
        "/api/v1/inquiries",
        json=VALID_INQUIRY,
    )

    assert create_response.status_code == 201

    inquiry_id = create_response.json()["id"]

    get_response = client.get(
        f"/api/v1/inquiries/{inquiry_id}"
    )

    assert get_response.status_code == 200

    response_body = get_response.json()

    assert response_body["id"] == inquiry_id
    assert response_body["requester_name"] == "Jordan Demo"
    assert response_body["requester_email"] == "jordan.demo@example.org"
    assert response_body["service_category"] == "Respite care"
    assert response_body["status"] == "new"


def test_get_inquiry_returns_404_for_missing_inquiry(
    client: TestClient,
) -> None:
    """A request for a nonexistent inquiry should return 404."""

    get_response = client.get(
        "/api/v1/inquiries/9999"
    )

    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": "Service inquiry not found."
    }


def test_update_inquiry_status_from_new_to_reviewing(
    client: TestClient,
) -> None:
    """An existing inquiry should allow its status to be updated."""

    create_response = client.post(
        "/api/v1/inquiries",
        json=VALID_INQUIRY,
    )

    assert create_response.status_code == 201

    inquiry_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/inquiries/{inquiry_id}/status",
        json={
            "status": "reviewing",
        },
    )

    assert update_response.status_code == 200

    response_body = update_response.json()

    assert response_body["id"] == inquiry_id
    assert response_body["status"] == "reviewing"

def test_update_inquiry_status_rejects_invalid_status(
    client: TestClient,
) -> None:
    """An unsupported inquiry status should be rejected."""

    create_response = client.post(
        "/api/v1/inquiries",
        json=VALID_INQUIRY,
    )

    assert create_response.status_code == 201

    inquiry_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/inquiries/{inquiry_id}/status",
        json={
            "status": "pending",
        },
    )

    assert update_response.status_code == 422



def test_update_inquiry_status_returns_404_for_missing_inquiry(
    client: TestClient,
) -> None:
    """A status update for a nonexistent inquiry should return 404."""

    update_response = client.patch(
        "/api/v1/inquiries/9999/status",
        json={
            "status": "reviewing",
        },
    )

    assert update_response.status_code == 404
    assert update_response.json() == {
        "detail": "Service inquiry not found."
    }

def test_updated_inquiry_status_is_returned_by_list_endpoint(
    client: TestClient,
) -> None:
    """A status change should remain visible when inquiries are listed."""

    create_response = client.post(
        "/api/v1/inquiries",
        json=VALID_INQUIRY,
    )

    assert create_response.status_code == 201

    inquiry_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/inquiries/{inquiry_id}/status",
        json={
            "status": "reviewing",
        },
    )

    assert update_response.status_code == 200

    list_response = client.get(
        "/api/v1/inquiries"
    )

    assert list_response.status_code == 200

    inquiries = list_response.json()

    assert inquiries[0]["id"] == inquiry_id
    assert inquiries[0]["status"] == "reviewing"
