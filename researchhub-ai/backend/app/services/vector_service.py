"""
vector_service.py – ChromaDB cosine-similarity search over paper chunk embeddings.

ChromaDB is used as the vector store instead of pgvector, providing full
cross-platform support without requiring PostgreSQL extensions.
Chunks are scoped to papers belonging to the requested workspace.
"""
import uuid
from typing import List

from sqlalchemy.orm import Session

from app.database.models import WorkspacePaper
from app.services.embedding_service import embedding_service
from app.services.chroma_service import chroma_service


class VectorService:
    def search_similar_chunks(
        self,
        db: Session,
        query: str,
        workspace_id: uuid.UUID,
        top_k: int = 5,
    ) -> List[dict]:
        """
        Convert *query* to an embedding, then find the most similar chunks
        that belong to papers inside *workspace_id* using ChromaDB.
        Returns a list of dicts with keys: chunk_id, chunk_text, paper_id, similarity.
        """
        query_embedding = embedding_service.generate_embedding(query)

        # Resolve paper_ids that belong to this workspace
        paper_ids = [
            str(wp.paper_id)
            for wp in db.query(WorkspacePaper)
            .filter(WorkspacePaper.workspace_id == workspace_id)
            .all()
        ]

        return chroma_service.search(
            query_embedding=query_embedding,
            paper_ids=paper_ids,
            top_k=top_k,
        )


vector_service = VectorService()

