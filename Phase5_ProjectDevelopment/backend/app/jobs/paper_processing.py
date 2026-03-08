"""
paper_processing.py – Background thread job that processes paper embeddings
without blocking the HTTP request that triggered the import.
"""
import threading
import uuid
import logging

logger = logging.getLogger(__name__)


class PaperProcessingJob:
    """Submit papers for async embedding generation."""

    def submit(self, paper_id: uuid.UUID, db_url: str) -> None:
        thread = threading.Thread(
            target=self._run,
            args=(paper_id, db_url),
            daemon=True,
            name=f"embed-{paper_id}",
        )
        thread.start()
        logger.info(f"Submitted paper {paper_id} for background processing.")

    def _run(self, paper_id: uuid.UUID, db_url: str) -> None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.services.paper_service import paper_service

        try:
            engine = create_engine(db_url, pool_pre_ping=True)
            Session = sessionmaker(bind=engine)
            db = Session()
            try:
                count = paper_service.process_paper_embeddings(db, paper_id)
                logger.info(f"[BG] Paper {paper_id}: {count} chunks created.")
            finally:
                db.close()
                engine.dispose()
        except Exception as exc:
            logger.error(f"[BG] Failed to process paper {paper_id}: {exc}")


paper_processing_job = PaperProcessingJob()
