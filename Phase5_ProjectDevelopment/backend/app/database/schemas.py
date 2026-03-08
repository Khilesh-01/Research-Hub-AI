from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
import uuid


# ── Auth / User ───────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserResponse(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# ── Workspace ─────────────────────────────────────────────────────────────────
class WorkspaceCreate(BaseModel):
    workspace_name: str
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    workspace_name: str
    description: Optional[str] = None
    created_at: datetime
    paper_count: Optional[int] = 0

    model_config = {"from_attributes": True}


# ── Paper ─────────────────────────────────────────────────────────────────────
class PaperImport(BaseModel):
    title: str
    authors: Optional[str] = None
    abstract: Optional[str] = None
    source: Optional[str] = None
    doi: Optional[str] = None
    pdf_url: Optional[str] = None
    published_date: Optional[str] = None


class PaperResponse(BaseModel):
    paper_id: uuid.UUID
    title: str
    authors: Optional[str] = None
    abstract: Optional[str] = None
    source: Optional[str] = None
    doi: Optional[str] = None
    pdf_url: Optional[str] = None
    published_date: Optional[str] = None
    imported_at: datetime

    model_config = {"from_attributes": True}


class PaperWithEmbeddingStatus(PaperResponse):
    """PaperResponse extended with embedding status from ChromaDB."""
    has_embeddings: bool = False
    chunk_count: int = 0


class PaperSearchResult(BaseModel):
    title: str
    authors: Optional[str] = None
    abstract: Optional[str] = None
    source: str
    doi: Optional[str] = None
    pdf_url: Optional[str] = None
    published_date: Optional[str] = None
    abs_url: Optional[str] = None        # arXiv abstract page link (None for PubMed)


class PaperSearchResponse(BaseModel):
    results: List[PaperSearchResult]
    total: int


# ── Chat ──────────────────────────────────────────────────────────────────────
class ChatSessionCreate(BaseModel):
    workspace_id: uuid.UUID
    title: Optional[str] = "New Chat"


class ChatSessionUpdate(BaseModel):
    title: str


class ChatSessionResponse(BaseModel):
    session_id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    title: Optional[str] = "New Chat"
    started_at: datetime
    message_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    message_id: uuid.UUID
    session_id: uuid.UUID
    role: str
    message_content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatQuery(BaseModel):
    session_id: uuid.UUID
    query: str


class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = []
    session_id: uuid.UUID


# ── Notes ─────────────────────────────────────────────────────────────────────
class NoteCreate(BaseModel):
    workspace_id: uuid.UUID
    paper_id: Optional[uuid.UUID] = None
    note_content: str


class NoteResponse(BaseModel):
    note_id: uuid.UUID
    workspace_id: uuid.UUID
    paper_id: Optional[uuid.UUID] = None
    note_content: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Tags ──────────────────────────────────────────────────────────────────────
class TagCreate(BaseModel):
    tag_name: str


class TagResponse(BaseModel):
    tag_id: uuid.UUID
    tag_name: str

    model_config = {"from_attributes": True}
