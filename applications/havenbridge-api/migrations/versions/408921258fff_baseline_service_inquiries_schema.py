"""baseline service inquiries schema

Revision ID: 408921258fff
Revises:
Create Date: 2026-09-09 11:06:41.573188
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "408921258fff"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create the initial HavenBridge service_inquiries schema.
    """

    op.create_table(
        "service_inquiries",

        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "requester_name",
            sa.String(length=120),
            nullable=False,
        ),

        sa.Column(
            "requester_email",
            sa.String(length=254),
            nullable=False,
        ),

        sa.Column(
            "service_category",
            sa.String(length=80),
            nullable=False,
        ),

        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=20),
            server_default="new",
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.CheckConstraint(
            "status IN ('new', 'reviewing', 'referred', 'closed')",
            name="ck_service_inquiries_status",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="service_inquiries_pkey",
        ),
    )

    op.create_index(
        "ix_service_inquiries_requester_email",
        "service_inquiries",
        ["requester_email"],
        unique=False,
    )

    op.create_index(
        "ix_service_inquiries_service_category",
        "service_inquiries",
        ["service_category"],
        unique=False,
    )

    op.create_index(
        "ix_service_inquiries_status",
        "service_inquiries",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """
    Remove the initial HavenBridge service_inquiries schema.
    """

    op.drop_index(
        "ix_service_inquiries_status",
        table_name="service_inquiries",
    )

    op.drop_index(
        "ix_service_inquiries_service_category",
        table_name="service_inquiries",
    )

    op.drop_index(
        "ix_service_inquiries_requester_email",
        table_name="service_inquiries",
    )

    op.drop_table("service_inquiries")
