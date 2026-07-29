"""
Service-inquiry routes for the HavenBridge API.

This file defines the inquiry endpoints, including:

    POST /api/v1/inquiries
        Creates a new service inquiry.

    GET /api/v1/inquiries
        Lists saved service inquiries.

This file only defines the routes. The routes become available to users when
main.py attaches this router with:

    app.include_router(inquiries.router)
"""

"""
Service-inquiry endpoints for the HavenBridge API.

This router connects:

    HTTP requests
        ↓
    Pydantic validation schemas
        ↓
    SQLAlchemy database model
        ↓
    PostgreSQL

The router is kept separate from main.py so inquiry-related functionality
can grow without making the main application file difficult to maintain.
"""

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ServiceInquiry
from app.schemas import (
    ServiceInquiryCreate,
    ServiceInquiryResponse,
)


logger = logging.getLogger(__name__)


# All endpoints in this router begin with /api/v1/inquiries.
#
# The tag groups these endpoints together in FastAPI's Swagger documentation.

# This router groups all service-inquiry endpoints.
# The prefix becomes the beginning of every route defined in this file.

router = APIRouter(
    prefix="/api/v1/inquiries",
    tags=["Service Inquiries"],
)


# This creates a reusable type for a database session.
#
# Depends(get_db) tells FastAPI:
# "Before running the endpoint, obtain a managed SQLAlchemy session."
DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

# Define the route that creates a new inquiry.
#
# Because the router prefix is /api/v1/inquiries and the decorator path is
# empty, the complete endpoint becomes:
#
# POST /api/v1/inquiries


@router.post(
    "",
    response_model=ServiceInquiryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a service inquiry",
)
def create_inquiry(
    inquiry_data: ServiceInquiryCreate,
    db: DatabaseSession,
) -> ServiceInquiry:
    """
    Validate and save a new service inquiry.

    inquiry_data:
        Contains JSON that was validated by ServiceInquiryCreate.

    db:
        Contains the SQLAlchemy database session supplied by get_db().

    The function returns the saved SQLAlchemy object. FastAPI converts it
    into the ServiceInquiryResponse JSON format.
    """

    # Convert the validated request schema into a database model object.
    inquiry = ServiceInquiry(
        requester_name=inquiry_data.requester_name,
        requester_email=str(inquiry_data.requester_email),
        service_category=inquiry_data.service_category,
        message=inquiry_data.message,
    )

    try:
        # Add the new object to the current database session.
        db.add(inquiry)

        # Save the transaction permanently in PostgreSQL.
        db.commit()

        # Reload the object so PostgreSQL-generated values such as ID,
        # status, created_at, and updated_at are available.
        db.refresh(inquiry)

    except SQLAlchemyError as exc:
        # Undo any incomplete database transaction.
        db.rollback()

        logger.exception(
            "Unable to create service inquiry."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save the service inquiry.",
        ) from exc

    return inquiry


# Define the route that lists existing inquiries.
#
# The complete endpoint becomes:
#
#     GET /api/v1/inquiries

@router.get(
    "",
    response_model=list[ServiceInquiryResponse],
    summary="List service inquiries",
)
def list_inquiries(
    db: DatabaseSession,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Maximum number of inquiries to return.",
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of inquiries to skip.",
        ),
    ] = 0,
) -> list[ServiceInquiry]:
    """
    Return saved service inquiries from PostgreSQL.

    Results are ordered from newest to oldest.

    limit:
        Controls the maximum number of records returned.

    offset:
        Controls how many records are skipped before returning results.
    """

    # Build a SQL SELECT statement.
    statement = (
        select(ServiceInquiry)
        .order_by(ServiceInquiry.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    try:
        # db.scalars() returns ServiceInquiry model objects rather than
        # lower-level database rows.
        inquiries = db.scalars(statement).all()

        return list(inquiries)

    except SQLAlchemyError as exc:
        logger.exception(
            "Unable to retrieve service inquiries."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve service inquiries.",
        ) from exc
