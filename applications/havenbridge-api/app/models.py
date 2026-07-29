"""
Database models for the HavenBridge API.

This file defines how HavenBridge information is stored in PostgreSQL.

The ServiceInquiry class maps Python attributes to columns in the
service_inquiries PostgreSQL table.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ServiceInquiry(Base):
    """
    Store one HavenBridge service inquiry in PostgreSQL.

    Each row represents a synthetic request for information, support,
    referral, or respiteBridge service inquiry in PostgreSQL.

    Each row-related services.
    """

    __tablename__ = "service_inquiries"

    # Restrict inquiry status to known workflow values.
    # This protects the database even when data does not come through FastAPI.
    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'reviewing', 'referred', 'closed')",
            name="ck_service_inquiries_status",
        ),
    )

    # PostgreSQL automatically generates a unique ID for each inquiry.
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # Name of the person submitting the inquiry.
    requester_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    # Email address used for follow-up communication.
    requester_email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
        index=True,
    )

    # General service or support category.
    service_category: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
    )

    # Main details supplied by the requester.
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Every newly created inquiry starts with the status "new".
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="new",
        index=True,
    )

    # PostgreSQL records when the inquiry was created.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # SQLAlchemy updates this timestamp when the record changes.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
