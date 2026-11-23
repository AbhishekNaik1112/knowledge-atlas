"""baseline schema: concepts, edges, sync_events, pgvector + FTS indexes

Revision ID: 0001_baseline
Revises:
Create Date: 2026-11-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "concepts",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("bundle", sa.Text(), nullable=False, server_default="default"),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resource", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "frontmatter",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english', "
                "coalesce(title,'') || ' ' || coalesce(description,'') || ' ' || coalesce(body,''))",
                persisted=True,
            ),
            nullable=True,
        ),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_concepts_type", "concepts", ["type"])
    op.create_index("idx_concepts_bundle", "concepts", ["bundle"])
    op.create_index("idx_concepts_tags", "concepts", ["tags"], postgresql_using="gin")
    op.create_index("idx_concepts_fts", "concepts", ["search_vector"], postgresql_using="gin")
    op.create_index(
        "idx_concepts_embed",
        "concepts",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_table(
        "edges",
        sa.Column(
            "source_id",
            sa.Text(),
            sa.ForeignKey("concepts.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("target_id", sa.Text(), primary_key=True),
        sa.Column("rel_type", sa.Text(), primary_key=True, server_default="link"),
        sa.Column("anchor_text", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("idx_edges_target", "edges", ["target_id"])

    op.create_table(
        "sync_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("bundle", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False, server_default="webhook"),
        sa.Column("commit_sha", sa.Text(), nullable=True),
        sa.Column("commit_message", sa.Text(), nullable=True),
        sa.Column("pusher", sa.Text(), nullable=True),
        sa.Column("ref", sa.Text(), nullable=True),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deleted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.Text(), nullable=False, server_default="ok"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("sync_events")
    op.drop_index("idx_edges_target", table_name="edges")
    op.drop_table("edges")
    op.drop_index("idx_concepts_embed", table_name="concepts")
    op.drop_index("idx_concepts_fts", table_name="concepts")
    op.drop_index("idx_concepts_tags", table_name="concepts")
    op.drop_index("idx_concepts_bundle", table_name="concepts")
    op.drop_index("idx_concepts_type", table_name="concepts")
    op.drop_table("concepts")
