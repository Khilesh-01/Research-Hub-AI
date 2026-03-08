"""Initial schema – enable pgvector and create all tables.

Revision ID: 001
Revises:
Create Date: 2026-03-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── pgvector extension ────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── users ─────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── workspaces ────────────────────────────────────────────────────────
    op.create_table(
        "workspaces",
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("workspace_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── papers ────────────────────────────────────────────────────────────
    op.create_table(
        "papers",
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors", sa.Text()),
        sa.Column("abstract", sa.Text()),
        sa.Column("source", sa.String(50)),
        sa.Column("doi", sa.String(255)),
        sa.Column("pdf_url", sa.Text()),
        sa.Column("published_date", sa.String(100)),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
    )

    # ── workspace_papers ──────────────────────────────────────────────────
    op.create_table(
        "workspace_papers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.workspace_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("papers.paper_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("workspace_id", "paper_id", name="uq_workspace_paper"),
    )

    # ── paper_chunks ──────────────────────────────────────────────────────
    op.create_table(
        "paper_chunks",
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("papers.paper_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        # pgvector column: 768 dimensions for all-mpnet-base-v2
        sa.Column("embedding", sa.Text()),   # Alembic doesn't know Vector; we rely on create_all
    )

    # ── chat_sessions ─────────────────────────────────────────────────────
    op.create_table(
        "chat_sessions",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.workspace_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("started_at", sa.DateTime(), nullable=False),
    )

    # ── chat_messages ─────────────────────────────────────────────────────
    op.create_table(
        "chat_messages",
        sa.Column("message_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("message_content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── notes ─────────────────────────────────────────────────────────────
    op.create_table(
        "notes",
        sa.Column("note_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.workspace_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("papers.paper_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note_content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── tags ──────────────────────────────────────────────────────────────
    op.create_table(
        "tags",
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tag_name", sa.String(100), unique=True, nullable=False),
    )

    # ── paper_tags ────────────────────────────────────────────────────────
    op.create_table(
        "paper_tags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("papers.paper_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tags.tag_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("paper_id", "tag_id", name="uq_paper_tag"),
    )


def downgrade() -> None:
    op.drop_table("paper_tags")
    op.drop_table("tags")
    op.drop_table("notes")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("paper_chunks")
    op.drop_table("workspace_papers")
    op.drop_table("papers")
    op.drop_table("workspaces")
    op.drop_table("users")
