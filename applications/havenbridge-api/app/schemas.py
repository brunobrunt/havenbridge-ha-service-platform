"""
Pydantic schemas for HavenBridge API requests and responses.

Schemas define the API contract.

They validate incoming JSON before it reaches PostgreSQL and control the
information returned to API clients.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ServiceInquiryCreate(BaseModel):
    """
    Validate the JSON body used to create a service inquiry.

    FastAPI automatically rejects missing fields, invalid email addresses,
    short messages, overly long values, and unexpected fields.
    """

    requester_name: str = Field(
        min_length=2,
        max_length=120,
        description="Name of the person submitting the inquiry.",
        examples=["Jordan Demo"],
    )

    requester_email: EmailStr = Field(
        description="Email address for follow-up communication.",
        examples=["jordan.demo@example.org"],
    )

    service_category: str = Field(
        min_length=2,
        max_length=80,
        description="General service or support category.",
        examples=["Respite care"],
    )

    message: str = Field(
        min_length=10,
        max_length=2000,
        description="Details about the requested information or support.",
        examples=[
            "I am requesting information about available respite services."
        ],
    )

    model_config = ConfigDict(
        # Remove accidental spaces from the beginning and end of text.
        str_strip_whitespace=True,

        # Reject fields that are not part of the approved request format.
        extra="forbid",
    )


class ServiceInquiryResponse(BaseModel):
    """
    Define the service-inquiry information returned by the API.

    from_attributes allows Pydantic to convert a SQLAlchemy model object
    into a JSON response.
    """

    id: int
    requester_name: str
    requester_email: EmailStr
    service_category: str
    message: str

    status: Literal[
        "new",
        "reviewing",
        "referred",
        "closed",
    ]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
