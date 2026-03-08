"""add emergency analytics tables

Revision ID: 650c4e2860a0
Revises: 5bc442a70e3b
Create Date: 2026-03-08 13:30:42.354993

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "650c4e2860a0"
down_revision: str | None = "5bc442a70e3b"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "emergency_analytics",
        sa.Column("emergency_id", sa.String(length=100), nullable=False),
        sa.Column("emergency_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acknowledged_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("arrived_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_estimated_eta_minutes", sa.Float(), nullable=True),
        sa.Column("avg_actual_eta_minutes", sa.Float(), nullable=True),
        sa.Column("avg_eta_error_minutes", sa.Float(), nullable=True),
        sa.Column("coordination_status", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.PrimaryKeyConstraint("emergency_id"),
    )
    op.create_index(
        "idx_emergency_analytics_status",
        "emergency_analytics",
        ["status"],
        unique=False,
        postgresql_using="btree",
    )
    op.create_index(
        "idx_emergency_analytics_type",
        "emergency_analytics",
        ["emergency_type"],
        unique=False,
        postgresql_using="btree",
    )
    op.create_index(
        "idx_emergency_analytics_dispatched",
        "emergency_analytics",
        ["dispatched_at"],
        unique=False,
        postgresql_using="btree",
    )

    op.create_table(
        "emergency_timeline",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("emergency_id", sa.String(length=100), nullable=False),
        sa.Column("phase", sa.String(length=30), nullable=False),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("event_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_emergency_timeline_emergency",
        "emergency_timeline",
        ["emergency_id"],
        unique=False,
        postgresql_using="btree",
    )
    op.create_index(
        "idx_emergency_timeline_event_ts",
        "emergency_timeline",
        ["event_ts"],
        unique=False,
        postgresql_using="btree",
    )
    op.create_index(
        "idx_emergency_timeline_emergency_ts",
        "emergency_timeline",
        ["emergency_id", "event_ts"],
        unique=False,
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "idx_emergency_timeline_emergency_ts",
        table_name="emergency_timeline",
        postgresql_using="btree",
    )
    op.drop_index(
        "idx_emergency_timeline_event_ts",
        table_name="emergency_timeline",
        postgresql_using="btree",
    )
    op.drop_index(
        "idx_emergency_timeline_emergency",
        table_name="emergency_timeline",
        postgresql_using="btree",
    )
    op.drop_table("emergency_timeline")

    op.drop_index(
        "idx_emergency_analytics_dispatched",
        table_name="emergency_analytics",
        postgresql_using="btree",
    )
    op.drop_index(
        "idx_emergency_analytics_type",
        table_name="emergency_analytics",
        postgresql_using="btree",
    )
    op.drop_index(
        "idx_emergency_analytics_status",
        table_name="emergency_analytics",
        postgresql_using="btree",
    )
    op.drop_table("emergency_analytics")
