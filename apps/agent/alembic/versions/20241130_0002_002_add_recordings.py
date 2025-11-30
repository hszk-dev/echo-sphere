"""Add recordings table and update existing tables.

Revision ID: 002
Revises: 001
Create Date: 2024-11-30

"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add recording_enabled column to sessions table
    op.add_column(
        "sessions",
        sa.Column("recording_enabled", sa.Boolean(), nullable=False, server_default="true"),
    )

    # Add timestamp_ms column to messages table
    op.add_column(
        "messages",
        sa.Column("timestamp_ms", sa.Integer(), nullable=True),
    )

    # Create recordings table
    op.create_table(
        "recordings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("egress_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="starting"),
        sa.Column("storage_bucket", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("playlist_url", sa.String(length=1024), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(op.f("ix_recordings_session_id"), "recordings", ["session_id"], unique=False)
    op.create_index(op.f("ix_recordings_egress_id"), "recordings", ["egress_id"], unique=True)
    op.create_index(op.f("ix_recordings_status"), "recordings", ["status"], unique=False)


def downgrade() -> None:
    # Drop recordings table and indexes
    op.drop_index(op.f("ix_recordings_status"), table_name="recordings")
    op.drop_index(op.f("ix_recordings_egress_id"), table_name="recordings")
    op.drop_index(op.f("ix_recordings_session_id"), table_name="recordings")
    op.drop_table("recordings")

    # Remove columns from existing tables
    op.drop_column("messages", "timestamp_ms")
    op.drop_column("sessions", "recording_enabled")
