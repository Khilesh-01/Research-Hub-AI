"""
chat_router.py – Chat session management and RAG-powered query endpoint.
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database import models, schemas
from app.utils.auth_utils import get_current_user
from app.agents.research_agent import research_agent

router = APIRouter()


@router.post(
    "/session",
    response_model=schemas.ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session for a workspace",
)
def create_session(
    data: schemas.ChatSessionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = (
        db.query(models.Workspace)
        .filter(
            models.Workspace.workspace_id == data.workspace_id,
            models.Workspace.user_id == current_user.user_id,
        )
        .first()
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    session = models.ChatSession(
        user_id=current_user.user_id,
        workspace_id=data.workspace_id,
        title=data.title or "New Chat",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    resp = schemas.ChatSessionResponse.model_validate(session)
    resp.message_count = 0
    return resp


@router.get(
    "/session/{workspace_id}",
    response_model=List[schemas.ChatSessionResponse],
    summary="List all chat sessions for a workspace (with message counts)",
)
def list_sessions(
    workspace_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.workspace_id == workspace_id,
            models.ChatSession.user_id == current_user.user_id,
        )
        .order_by(models.ChatSession.started_at.desc())
        .all()
    )

    result = []
    for s in sessions:
        count = (
            db.query(models.ChatMessage)
            .filter(models.ChatMessage.session_id == s.session_id)
            .count()
        )
        resp = schemas.ChatSessionResponse.model_validate(s)
        resp.message_count = count
        result.append(resp)
    return result


@router.patch(
    "/session/{session_id}",
    response_model=schemas.ChatSessionResponse,
    summary="Rename a chat session",
)
def rename_session(
    session_id: uuid.UUID,
    data: schemas.ChatSessionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.session_id == session_id,
            models.ChatSession.user_id == current_user.user_id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    session.title = data.title
    db.commit()
    db.refresh(session)
    count = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .count()
    )
    resp = schemas.ChatSessionResponse.model_validate(session)
    resp.message_count = count
    return resp


@router.delete(
    "/session/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat session and all its messages",
)
def delete_session(
    session_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.session_id == session_id,
            models.ChatSession.user_id == current_user.user_id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    db.delete(session)
    db.commit()


@router.post(
    "/query",
    response_model=schemas.ChatResponse,
    summary="Send a research query to the AI agent",
)
def query(
    chat_query: schemas.ChatQuery,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.session_id == chat_query.session_id,
            models.ChatSession.user_id == current_user.user_id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    result = research_agent.process_query(
        db=db,
        session_id=chat_query.session_id,
        query=chat_query.query,
        workspace_id=session.workspace_id,
    )

    # Auto-title the session after the first user message
    msg_count = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == chat_query.session_id)
        .count()
    )
    if msg_count <= 2 and (not session.title or session.title == "New Chat"):
        auto_title = chat_query.query[:60].strip()
        if len(chat_query.query) > 60:
            auto_title += "…"
        session.title = auto_title
        db.commit()

    return schemas.ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        session_id=chat_query.session_id,
    )


@router.get(
    "/messages/{session_id}",
    response_model=List[schemas.ChatMessageResponse],
    summary="Get messages for a chat session",
)
def get_messages(
    session_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.session_id == session_id,
            models.ChatSession.user_id == current_user.user_id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )
