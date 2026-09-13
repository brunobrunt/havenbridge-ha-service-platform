"""add inquiry status history

Revision ID: 7b1c4de0f49c
Revises: 0725ffe2bda2
Create Date: 2026-09-13 08:23:02.235881

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b1c4de0f49c"
down_revision: Union[str, Sequence[str], None] = "0725ffe2bda2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the inquiry status history table."""

    op.create_table(
        "inquiry_status_history",

        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "inquiry_id",
            sa.BigInteger(),
            nullable=False,
        ),

        sa.Column(
            "old_status",
            sa.String(length=20),
            nullable=True,
        ),

        sa.Column(
            "new_status",
            sa.String(length=20),
            nullable=False,
        ),

        sa.Column(
            "changed_by",
            sa.String(length=120),
            nullable=True,
        ),

        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["inquiry_id"],
            ["service_inquiries.id"],
            name="fk_inquiry_status_history_inquiry_id_service_inquiries",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_inquiry_status_history_inquiry_id",
        "inquiry_status_history",
        ["inquiry_id"],
        unique=False,
    )

    op.create_index(
        "ix_inquiry_status_history_new_status",
        "inquiry_status_history",
        ["new_status"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the inquiry status history table."""

    op.drop_index(
        "ix_inquiry_status_history_new_status",
        table_name="inquiry_status_history",
    )

    op.drop_index(
        "ix_inquiry_status_history_inquiry_id",
        table_name="inquiry_status_history",
    )

    op.drop_table(
        "inquiry_status_history",
    )
