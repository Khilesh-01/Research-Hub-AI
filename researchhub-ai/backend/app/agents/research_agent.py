"""
research_agent.py – Agentic RAG loop: retrieve → augment → generate.
"""
import uuid
import logging
from typing import List

from sqlalchemy.orm import Session

from app.database.models import ChatMessage, WorkspacePaper, Paper
from app.services.vector_service import vector_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Orchestrates the full RAG pipeline:
    1. Retrieve relevant chunks from pgvector using semantic similarity.
    2. Fall back to paper abstracts if no embeddings exist yet.
    3. Build a context-aware prompt and invoke the Groq LLM.
    4. Persist user message + assistant reply in the database.
    """

    def process_query(
        self,
        db: Session,
        session_id: uuid.UUID,
        query: str,
        workspace_id: uuid.UUID,
    ) -> dict:
        # 1. Fetch chat history for multi-turn context
        chat_history = self._load_history(db, session_id)

        # 2. Semantic retrieval
        chunks = vector_service.search_similar_chunks(
            db=db,
            query=query,
            workspace_id=workspace_id,
            top_k=5,
        )
        context_texts: List[str] = [c["chunk_text"] for c in chunks]
        source_ids: List[str] = list({c["paper_id"] for c in chunks})

        # 3. Fallback → abstract summaries when no embeddings are available
        if not context_texts:
            logger.info("No vector chunks found — falling back to abstracts.")
            context_texts = self._abstract_context(db, workspace_id)

        # 4. Generate answer
        answer = llm_service.generate_research_answer(
            query=query,
            context_chunks=context_texts,
            chat_history=chat_history,
        )

        # 5. Persist messages
        self._save_message(db, session_id, "user", query)
        self._save_message(db, session_id, "assistant", answer)

        return {
            "answer": answer,
            "sources": source_ids,
            "session_id": str(session_id),
        }

    # ── Helpers ────────────────────────────────────────────────────────────
    def _load_history(self, db: Session, session_id: uuid.UUID) -> List[dict]:
        msgs = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
            .all()
        )
        return [
            {"role": m.role, "content": m.message_content}
            for m in reversed(msgs)
        ]

    def _abstract_context(
        self, db: Session, workspace_id: uuid.UUID
    ) -> List[str]:
        wps = (
            db.query(WorkspacePaper)
            .filter(WorkspacePaper.workspace_id == workspace_id)
            .limit(10)
            .all()
        )
        texts: List[str] = []
        for wp in wps:
            p = db.query(Paper).filter(Paper.paper_id == wp.paper_id).first()
            if p and p.abstract:
                texts.append(f"**{p.title}**\n{p.abstract}")
        return texts[:5]

    def _save_message(
        self,
        db: Session,
        session_id: uuid.UUID,
        role: str,
        content: str,
    ) -> None:
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            message_content=content,
        )
        db.add(msg)
        db.commit()


research_agent = ResearchAgent()
