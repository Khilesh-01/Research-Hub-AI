import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey,
    Integer, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.database import Base


# ── Users ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workspaces = relationship(
        "Workspace", back_populates="user", cascade="all, delete-orphan"
    )
    chat_sessions = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )


# ── Workspaces ────────────────────────────────────────────────────────────────
class Workspace(Base):
    __tablename__ = "workspaces"

    workspace_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="workspaces")
    workspace_papers = relationship(
        "WorkspacePaper", back_populates="workspace", cascade="all, delete-orphan"
    )
    chat_sessions = relationship(
        "ChatSession", back_populates="workspace", cascade="all, delete-orphan"
    )
    notes = relationship(
        "Note", back_populates="workspace", cascade="all, delete-orphan"
    )


# ── Papers ────────────────────────────────────────────────────────────────────
class Paper(Base):
    __tablename__ = "papers"

    paper_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    authors = Column(Text)
    abstract = Column(Text)
    source = Column(String(50))          # 'arxiv' | 'pubmed'
    doi = Column(String(255))
    pdf_url = Column(Text)
    published_date = Column(String(100))
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    workspace_papers = relationship(
        "WorkspacePaper", back_populates="paper", cascade="all, delete-orphan"
    )
    chunks = relationship(
        "PaperChunk", back_populates="paper", cascade="all, delete-orphan"
    )
    notes = relationship("Note", back_populates="paper")
    paper_tags = relationship(
        "PaperTag", back_populates="paper", cascade="all, delete-orphan"
    )


# ── Workspace ↔ Paper join table ──────────────────────────────────────────────
class WorkspacePaper(Base):
    __tablename__ = "workspace_papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.workspace_id", ondelete="CASCADE"),
        nullable=False,
    )
    paper_id = Column(
        UUID(as_uuid=True),
        ForeignKey("papers.paper_id", ondelete="CASCADE"),
        nullable=False,
    )
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("workspace_id", "paper_id", name="uq_workspace_paper"),
    )

    workspace = relationship("Workspace", back_populates="workspace_papers")
    paper = relationship("Paper", back_populates="workspace_papers")


# ── Paper Chunks (vector store) ───────────────────────────────────────────────
class PaperChunk(Base):
    __tablename__ = "paper_chunks"

    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(
        UUID(as_uuid=True),
        ForeignKey("papers.paper_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_text = Column(Text, nullable=False)
    # Embeddings are stored in ChromaDB (not PostgreSQL) for cross-platform support

    paper = relationship("Paper", back_populates="chunks")


# ── Chat Sessions ─────────────────────────────────────────────────────────────
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.workspace_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), default="New Chat", nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="chat_sessions")
    workspace = relationship("Workspace", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )


# ── Chat Messages ─────────────────────────────────────────────────────────────
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(50), nullable=False)     # 'user' | 'assistant'
    message_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="messages")


# ── Notes ─────────────────────────────────────────────────────────────────────
class Note(Base):
    __tablename__ = "notes"

    note_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.workspace_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id = Column(
        UUID(as_uuid=True),
        ForeignKey("papers.paper_id", ondelete="SET NULL"),
        nullable=True,
    )
    note_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="notes")
    paper = relationship("Paper", back_populates="notes")


# ── Tags ──────────────────────────────────────────────────────────────────────
class Tag(Base):
    __tablename__ = "tags"

    tag_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tag_name = Column(String(100), unique=True, nullable=False)

    paper_tags = relationship(
        "PaperTag", back_populates="tag", cascade="all, delete-orphan"
    )


# ── Paper ↔ Tag join table ────────────────────────────────────────────────────
class PaperTag(Base):
    __tablename__ = "paper_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(
        UUID(as_uuid=True),
        ForeignKey("papers.paper_id", ondelete="CASCADE"),
        nullable=False,
    )
    tag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tags.tag_id", ondelete="CASCADE"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("paper_id", "tag_id", name="uq_paper_tag"),
    )

    paper = relationship("Paper", back_populates="paper_tags")
    tag = relationship("Tag", back_populates="paper_tags")
