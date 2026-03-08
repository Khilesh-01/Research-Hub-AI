"""
workspace_router.py – CRUD for workspaces, paper membership, and notes.
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database import models, schemas
from app.utils.auth_utils import get_current_user
from app.services.paper_service import paper_service

router = APIRouter()


# ── Workspace CRUD ────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=schemas.WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a workspace",
)
def create_workspace(
    workspace: schemas.WorkspaceCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_ws = models.Workspace(
        user_id=current_user.user_id,
        workspace_name=workspace.workspace_name,
        description=workspace.description,
    )
    db.add(db_ws)
    db.commit()
    db.refresh(db_ws)

    resp = schemas.WorkspaceResponse.model_validate(db_ws)
    resp.paper_count = 0
    return resp


@router.get(
    "/",
    response_model=List[schemas.WorkspaceResponse],
    summary="List all workspaces for current user",
)
def list_workspaces(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspaces = (
        db.query(models.Workspace)
        .filter(models.Workspace.user_id == current_user.user_id)
        .order_by(models.Workspace.created_at.desc())
        .all()
    )
    result = []
    for ws in workspaces:
        count = (
            db.query(models.WorkspacePaper)
            .filter(models.WorkspacePaper.workspace_id == ws.workspace_id)
            .count()
        )
        resp = schemas.WorkspaceResponse.model_validate(ws)
        resp.paper_count = count
        result.append(resp)
    return result


@router.get(
    "/{workspace_id}",
    response_model=schemas.WorkspaceResponse,
    summary="Get a workspace",
)
def get_workspace(
    workspace_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = _get_owned_ws(db, workspace_id, current_user.user_id)
    count = (
        db.query(models.WorkspacePaper)
        .filter(models.WorkspacePaper.workspace_id == workspace_id)
        .count()
    )
    resp = schemas.WorkspaceResponse.model_validate(ws)
    resp.paper_count = count
    return resp


@router.put(
    "/{workspace_id}",
    response_model=schemas.WorkspaceResponse,
    summary="Update a workspace",
)
def update_workspace(
    workspace_id: uuid.UUID,
    data: schemas.WorkspaceCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = _get_owned_ws(db, workspace_id, current_user.user_id)
    ws.workspace_name = data.workspace_name
    ws.description = data.description
    db.commit()
    db.refresh(ws)
    count = (
        db.query(models.WorkspacePaper)
        .filter(models.WorkspacePaper.workspace_id == workspace_id)
        .count()
    )
    resp = schemas.WorkspaceResponse.model_validate(ws)
    resp.paper_count = count
    return resp


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workspace",
)
def delete_workspace(
    workspace_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = _get_owned_ws(db, workspace_id, current_user.user_id)
    db.delete(ws)
    db.commit()


# ── Paper membership ──────────────────────────────────────────────────────────

@router.get(
    "/{workspace_id}/papers",
    response_model=List[schemas.PaperWithEmbeddingStatus],
    summary="List papers in a workspace with embedding status",
)
def list_workspace_papers(
    workspace_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_ws(db, workspace_id, current_user.user_id)
    papers = paper_service.get_workspace_papers(db, workspace_id)

    from app.services.chroma_service import chroma_service
    result = []
    for p in papers:
        count = chroma_service.get_chunk_count(str(p.paper_id))
        r = schemas.PaperWithEmbeddingStatus.model_validate(p)
        r.has_embeddings = count > 0
        r.chunk_count = count
        result.append(r)
    return result


@router.delete(
    "/{workspace_id}/papers/{paper_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a paper from a workspace",
)
def remove_paper(
    workspace_id: uuid.UUID,
    paper_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_ws(db, workspace_id, current_user.user_id)
    wp = (
        db.query(models.WorkspacePaper)
        .filter(
            models.WorkspacePaper.workspace_id == workspace_id,
            models.WorkspacePaper.paper_id == paper_id,
        )
        .first()
    )
    if not wp:
        raise HTTPException(status_code=404, detail="Paper not in workspace.")
    db.delete(wp)
    db.commit()


# ── Notes ─────────────────────────────────────────────────────────────────────

@router.post(
    "/{workspace_id}/notes",
    response_model=schemas.NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a note",
)
def create_note(
    workspace_id: uuid.UUID,
    note: schemas.NoteCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_ws(db, workspace_id, current_user.user_id)
    db_note = models.Note(
        workspace_id=workspace_id,
        paper_id=note.paper_id,
        note_content=note.note_content,
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


@router.get(
    "/{workspace_id}/notes",
    response_model=List[schemas.NoteResponse],
    summary="List notes in a workspace",
)
def list_notes(
    workspace_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_ws(db, workspace_id, current_user.user_id)
    return (
        db.query(models.Note)
        .filter(models.Note.workspace_id == workspace_id)
        .order_by(models.Note.created_at.desc())
        .all()
    )


@router.delete(
    "/{workspace_id}/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note",
)
def delete_note(
    workspace_id: uuid.UUID,
    note_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_ws(db, workspace_id, current_user.user_id)
    note = (
        db.query(models.Note)
        .filter(
            models.Note.note_id == note_id,
            models.Note.workspace_id == workspace_id,
        )
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    db.delete(note)
    db.commit()


# ── Helper ────────────────────────────────────────────────────────────────────
def _get_owned_ws(
    db: Session, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> models.Workspace:
    ws = (
        db.query(models.Workspace)
        .filter(
            models.Workspace.workspace_id == workspace_id,
            models.Workspace.user_id == user_id,
        )
        .first()
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return ws
