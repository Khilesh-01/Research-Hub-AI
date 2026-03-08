"""
paper_service.py – Business logic for importing, storing, and processing papers.
"""
import uuid
import logging
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.database.models import Paper, WorkspacePaper, PaperChunk
from app.database.schemas import PaperImport
from app.services.embedding_service import embedding_service
from app.utils.pdf_parser import pdf_parser
from app.utils.chunking import text_chunker

logger = logging.getLogger(__name__)


class PaperService:

    # ── Import ─────────────────────────────────────────────────────────────
    def import_paper(self, db: Session, paper_data: PaperImport) -> Paper:
        """Persist paper metadata and return the ORM object."""
        db_paper = Paper(
            title=paper_data.title,
            authors=paper_data.authors,
            abstract=paper_data.abstract,
            source=paper_data.source,
            doi=paper_data.doi,
            pdf_url=paper_data.pdf_url,
            published_date=paper_data.published_date,
        )
        db.add(db_paper)
        db.commit()
        db.refresh(db_paper)
        logger.info(f"Imported paper: {db_paper.paper_id} – {db_paper.title[:60]}")
        return db_paper

    # ── Workspace assignment ───────────────────────────────────────────────
    def add_paper_to_workspace(
        self, db: Session, paper_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> WorkspacePaper:
        existing = (
            db.query(WorkspacePaper)
            .filter(
                WorkspacePaper.workspace_id == workspace_id,
                WorkspacePaper.paper_id == paper_id,
            )
            .first()
        )
        if existing:
            return existing

        wp = WorkspacePaper(workspace_id=workspace_id, paper_id=paper_id)
        db.add(wp)
        db.commit()
        db.refresh(wp)
        return wp

    def get_workspace_papers(
        self, db: Session, workspace_id: uuid.UUID
    ) -> List[Paper]:
        wps = (
            db.query(WorkspacePaper)
            .filter(WorkspacePaper.workspace_id == workspace_id)
            .options(joinedload(WorkspacePaper.paper))
            .all()
        )
        return [wp.paper for wp in wps if wp.paper is not None]

    # ── Embeddings ─────────────────────────────────────────────────────────
    def process_paper_embeddings(
        self, db: Session, paper_id: uuid.UUID
    ) -> int:
        """
        1. Try to fetch + parse the paper PDF.
        2. Fall back to abstract if PDF unavailable.
        3. Chunk the text, generate embeddings, store PaperChunk rows.
        Returns the number of chunks created.
        """
        paper = db.query(Paper).filter(Paper.paper_id == paper_id).first()
        if paper is None:
            return 0

        text: Optional[str] = None

        if paper.pdf_url:
            logger.info(f"Fetching PDF for paper {paper_id}…")
            text = pdf_parser.extract_text_from_url(paper.pdf_url)

        if not text or len(text.strip()) < 200:
            # Fallback to abstract
            if paper.abstract:
                text = f"{paper.title}\n\n{paper.abstract}"
            else:
                logger.warning(f"No content available for paper {paper_id}")
                return 0

        return self._store_chunks(db, paper, text)

    def _store_chunks(self, db: Session, paper: Paper, text: str) -> int:
        # Remove old chunks from PostgreSQL
        db.query(PaperChunk).filter(
            PaperChunk.paper_id == paper.paper_id
        ).delete(synchronize_session="fetch")
        db.flush()

        chunks = text_chunker.chunk_text(text)
        if not chunks:
            return 0

        # Persist chunk text in PostgreSQL for reference
        chunk_objs = [
            PaperChunk(paper_id=paper.paper_id, chunk_text=chunk)
            for chunk in chunks
        ]
        db.add_all(chunk_objs)
        db.flush()
        db.commit()

        # Generate embeddings and store in ChromaDB
        embeddings = embedding_service.generate_embeddings_batch(chunks)
        from app.services.chroma_service import chroma_service
        count = chroma_service.store_chunks(
            paper_id=str(paper.paper_id),
            chunks=chunks,
            embeddings=embeddings,
        )
        logger.info(f"Stored {count} chunks for paper {paper.paper_id}")
        return count


paper_service = PaperService()
