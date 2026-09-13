"""add inquiry foreign keys

Revision ID: 0725ffe2bda2
Revises: 96a173d66667
Create Date: 2026-09-12 12:52:37.369825

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0725ffe2bda2"
down_revision: Union[str, Sequence[str], None] = "96a173d66667"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add relational foreign-key columns to service inquiries."""

    # Add nullable relationship columns first.
    #
    # They are nullable so the existing HavenBridge validation rows remain
    # valid while relational data is introduced gradually.
    op.add_column(
        "service_inquiries",
        sa.Column(
            "client_id",
            sa.BigInteger(),
            nullable=True,
        ),
    )

    op.add_column(
        "service_inquiries",
        sa.Column(
            "category_id",
            sa.BigInteger(),
            nullable=True,
        ),
    )

    op.add_column(
        "service_inquiries",
        sa.Column(
            "coordinator_id",
            sa.BigInteger(),
            nullable=True,
        ),
    )

    # Connect service_inquiries.client_id to clients.id.
    op.create_foreign_key(
        "fk_service_inquiries_client_id_clients",
        "service_inquiries",
        "clients",
        ["client_id"],
        ["id"],
    )

    # Connect service_inquiries.category_id to service_categories.id.
    op.create_foreign_key(
        "fk_service_inquiries_category_id_service_categories",
        "service_inquiries",
        "service_categories",
        ["category_id"],
        ["id"],
    )

    # Connect service_inquiries.coordinator_id to coordinators.id.
    op.create_foreign_key(
        "fk_service_inquiries_coordinator_id_coordinators",
        "service_inquiries",
        "coordinators",
        ["coordinator_id"],
        ["id"],
    )


def downgrade() -> None:
    """Remove inquiry relationships and their foreign-key columns."""

    # Foreign-key constraints must be removed before their columns.
    op.drop_constraint(
        "fk_service_inquiries_coordinator_id_coordinators",
        "service_inquiries",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_service_inquiries_category_id_service_categories",
        "service_inquiries",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_service_inquiries_client_id_clients",
        "service_inquiries",
        type_="foreignkey",
    )

    op.drop_column(
        "service_inquiries",
        "coordinator_id",
    )

    op.drop_column(
        "service_inquiries",
        "category_id",
    )

    op.drop_column(
        "service_inquiries",
        "client_id",
    )
