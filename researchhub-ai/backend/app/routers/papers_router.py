"""
papers_router.py – Search, import, manage research papers, and serve PDFs.
"""
import os
import uuid
from typing import Optional

import requests as http_requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database import models, schemas
from app.utils.auth_utils import get_current_user
from app.services.search_service import search_service
from app.services.paper_service import paper_service
from app.jobs.paper_processing import paper_processing_job

router = APIRouter()

_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://Smartbridge:Smartbridge123@localhost:5432/ResearchHub",
)


@router.get(
    "/search",
    response_model=schemas.PaperSearchResponse,
    summary="Search arXiv / PubMed",
)
def search_papers(
    query: str,
    source: str = "all",
    max_results: int = 10,
    _: models.User = Depends(get_current_user),
):
    if len(query.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be at least 2 characters.",
        )
    results = search_service.search(
        query=query, source=source, max_results=max_results
    )
    return schemas.PaperSearchResponse(
        results=[schemas.PaperSearchResult(**r) for r in results],
        total=len(results),
    )


@router.post(
    "/import",
    response_model=schemas.PaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import a paper into the database",
)
def import_paper(
    paper: schemas.PaperImport,
    workspace_id: Optional[uuid.UUID] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_paper = paper_service.import_paper(db, paper)

    if workspace_id:
        ws = (
            db.query(models.Workspace)
            .filter(
                models.Workspace.workspace_id == workspace_id,
                models.Workspace.user_id == current_user.user_id,
            )
            .first()
        )
        if ws:
            paper_service.add_paper_to_workspace(db, db_paper.paper_id, workspace_id)

    # Kick off background embedding generation
    paper_processing_job.submit(db_paper.paper_id, _DB_URL)

    return db_paper


@router.post(
    "/{paper_id}/workspace/{workspace_id}",
    summary="Add an existing paper to a workspace",
)
def add_to_workspace(
    paper_id: uuid.UUID,
    workspace_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = (
        db.query(models.Workspace)
        .filter(
            models.Workspace.workspace_id == workspace_id,
            models.Workspace.user_id == current_user.user_id,
        )
        .first()
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    paper = db.query(models.Paper).filter(models.Paper.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")

    wp = paper_service.add_paper_to_workspace(db, paper_id, workspace_id)
    # Trigger embedding generation if not already done
    paper_processing_job.submit(paper_id, _DB_URL)
    return {"message": "Paper added to workspace.", "id": wp.id}


@router.get(
    "/{paper_id}",
    response_model=schemas.PaperResponse,
    summary="Get paper details",
)
def get_paper(
    paper_id: uuid.UUID,
    _: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = db.query(models.Paper).filter(models.Paper.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return paper


@router.get(
    "/{paper_id}/embedding-status",
    summary="Check if embeddings are built for a paper",
)
def embedding_status(
    paper_id: uuid.UUID,
    _: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = db.query(models.Paper).filter(models.Paper.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")

    from app.services.chroma_service import chroma_service
    count = chroma_service.get_chunk_count(str(paper_id))
    return {
        "paper_id": str(paper_id),
        "has_embeddings": count > 0,
        "chunk_count": count,
    }


@router.post(
    "/{paper_id}/process-embeddings",
    summary="Manually trigger embedding generation for a paper",
)
def process_embeddings(
    paper_id: uuid.UUID,
    _: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = db.query(models.Paper).filter(models.Paper.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    count = paper_service.process_paper_embeddings(db, paper_id)
    return {"message": f"Generated {count} chunks.", "chunk_count": count}


@router.get(
    "/{paper_id}/pdf",
    summary="Proxy PDF download/view for a paper",
)
def proxy_pdf(
    paper_id: uuid.UUID,
    download: bool = False,
    _: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch the paper's PDF from its stored URL and stream it through the backend.
    This handles CORS issues and provides a consistent download experience.
    Set ?download=true to force browser download instead of inline viewing.
    """
    paper = db.query(models.Paper).filter(models.Paper.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    if not paper.pdf_url:
        raise HTTPException(status_code=404, detail="No PDF URL available for this paper.")

    # Normalise arXiv PDF URLs (abs → pdf)
    pdf_url = paper.pdf_url
    if "arxiv.org/abs/" in pdf_url:
        pdf_url = pdf_url.replace("arxiv.org/abs/", "arxiv.org/pdf/")

    try:
        resp = http_requests.get(
            pdf_url,
            headers={"User-Agent": "ResearchHub/1.0"},
            stream=True,
            timeout=30,
        )
        resp.raise_for_status()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch PDF from source: {exc}",
        )

    disposition = "attachment" if download else "inline"
    safe_title = "".join(c for c in paper.title[:50] if c.isalnum() or c in " -_")
    filename = f"{safe_title}.pdf"

    def iter_content():
        for chunk in resp.iter_content(chunk_size=8192):
            yield chunk

    return StreamingResponse(
        iter_content(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "Cache-Control": "public, max-age=3600",
        },
    )



@router.get(
    "/search",
    response_model=schemas.PaperSearchResponse,
    summary="Search arXiv / PubMed",
)
def search_papers(
    query: str,
    source: str = "all",
    max_results: int = 10,
    _: models.User = Depends(get_current_user),
):
    if len(query.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be at least 2 characters.",
        )
    results = search_service.search(
        query=query, source=source, max_results=max_results
    )
    return schemas.PaperSearchResponse(
        results=[schemas.PaperSearchResult(**r) for r in results],
        total=len(results),
    )


@router.post(
    "/import",
    response_model=schemas.PaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import a paper into the database",
)
def import_paper(
    paper: schemas.PaperImport,
    workspace_id: Optional[uuid.UUID] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_paper = paper_service.import_paper(db, paper)

    if workspace_id:
        ws = (
            db.query(models.Workspace)
            .filter(
                models.Workspace.workspace_id == workspace_id,
                models.Workspace.user_id == current_user.user_id,
            )
            .first()
        )
        if ws:
            paper_service.add_paper_to_workspace(db, db_paper.paper_id, workspace_id)

    # Kick off background embedding generation
    paper_processing_job.submit(db_paper.paper_id, _DB_URL)

    return db_paper


@router.post(
    "/{paper_id}/workspace/{workspace_id}",
    summary="Add an existing paper to a workspace",
)
def add_to_workspace(
    paper_id: uuid.UUID,
    workspace_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = (
        db.query(models.Workspace)
        .filter(
            models.Workspace.workspace_id == workspace_id,
            models.Workspace.user_id == current_user.user_id,
        )
        .first()
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    paper = db.query(models.Paper).filter(models.Paper.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")

    wp = paper_service.add_paper_to_workspace(db, paper_id, workspace_id)
    return {"message": "Paper added to workspace.", "id": wp.id}


@router.get(
    "/{paper_id}",
    response_model=schemas.PaperResponse,
    summary="Get paper details",
)
def get_paper(
    paper_id: uuid.UUID,
    _: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = db.query(models.Paper).filter(models.Paper.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return paper


@router.post(
    "/{paper_id}/process-embeddings",
    summary="Manually trigger embedding generation for a paper",
)
def process_embeddings(
    paper_id: uuid.UUID,
    _: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = db.query(models.Paper).filter(models.Paper.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    count = paper_service.process_paper_embeddings(db, paper_id)
    return {"message": f"Generated {count} chunks.", "chunk_count": count}
