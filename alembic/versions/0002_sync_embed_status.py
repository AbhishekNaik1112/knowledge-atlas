"""add embedded_count and embed_status to sync_events

Revision ID: 0002_sync_embed_status
Revises: 0001_baseline
Create Date: 2026-11-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_sync_embed_status"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sync_events",
        sa.Column("embedded_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "sync_events",
        sa.Column("embed_status", sa.Text(), nullable=False, server_default="skipped"),
    )


def downgrade() -> None:
    op.drop_column("sync_events", "embed_status")
    op.drop_column("sync_events", "embedded_count")
