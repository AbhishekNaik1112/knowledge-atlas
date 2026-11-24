"""add embed_detail to sync_events

Revision ID: 0003_sync_embed_detail
Revises: 0002_sync_embed_status
Create Date: 2026-11-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_sync_embed_detail"
down_revision = "0002_sync_embed_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sync_events", sa.Column("embed_detail", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("sync_events", "embed_detail")
