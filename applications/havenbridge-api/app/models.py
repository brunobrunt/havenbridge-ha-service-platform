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
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class ServiceCategory(Base):
    """
    Store one HavenBridge service category.

    Examples include home care, respite care, disability support,
    family support, residential care, and community access.
    """

    __tablename__ = "service_categories"

    # Unique database identifier for the category.
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # Human-readable service name.
    name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        unique=True,
        index=True,
    )

    # Longer explanation of the service category.
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Record when the category was created.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

class Client(Base):
    """
    Store one synthetic HavenBridge client.

    Client records represent fictitious people used for development,
    demonstrations, API testing, observability, and later AI validation.
    """

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
        unique=True,
        index=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Coordinator(Base):
    """
    Store one synthetic HavenBridge service coordinator.

    Coordinators represent staff members who can be assigned to
    service inquiries.
    """

    __tablename__ = "coordinators"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
        unique=True,
        index=True,
    )

    team: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

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

    # Optional relationship to the synthetic client record.
    client_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("clients.id"),
        nullable=True,
    )

    # Optional relationship to the normalized service category.
    category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("service_categories.id"),
        nullable=True,
    )

    # Optional coordinator assigned to handle the inquiry.
    coordinator_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("coordinators.id"),
        nullable=True,
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
class InquiryStatusHistory(Base):
    """
    Record one status change for a HavenBridge service inquiry.

    This preserves workflow history instead of keeping only the
    inquiry's current status.
    """

    __tablename__ = "inquiry_status_history"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # Inquiry whose status changed.
    inquiry_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("service_inquiries.id"),
        nullable=False,
        index=True,
    )

    # Previous status. NULL is allowed for the first history record.
    old_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # New status after the change.
    new_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    # Identifies what initiated the change.
    # Examples: "seed", "api", or later an authenticated staff identity.
    changed_by: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    # PostgreSQL records when the status transition occurred.
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
