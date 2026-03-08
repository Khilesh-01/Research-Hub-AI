"""
chroma_service.py – ChromaDB-based persistent vector store for paper embeddings.

Uses ChromaDB as a lightweight local vector database, replacing pgvector
which requires a PostgreSQL extension not available in all environments.
Embeddings are stored per-paper and searched filtered by workspace paper IDs.
"""
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Persistent storage path: backend/chroma_data/
CHROMA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data")
)


class ChromaService:
    """Singleton wrapper around ChromaDB for paper chunk embeddings."""

    _instance: "ChromaService | None" = None
    _client = None
    _collection = None

    def __new__(cls) -> "ChromaService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_collection(self):
        if self._collection is None:
            import chromadb  # lazy import

            os.makedirs(CHROMA_PATH, exist_ok=True)
            self._client = chromadb.PersistentClient(path=CHROMA_PATH)
            self._collection = self._client.get_or_create_collection(
                name="paper_chunks",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                f"ChromaDB ready at {CHROMA_PATH} "
                f"— {self._collection.count()} chunks stored."
            )
        return self._collection

    # ── Write ──────────────────────────────────────────────────────────────

    def store_chunks(
        self,
        paper_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
    ) -> int:
        """Upsert embeddings for a paper's chunks, replacing any existing ones."""
        if not chunks:
            return 0

        collection = self._get_collection()

        # Delete stale chunks for this paper before re-inserting
        existing = collection.get(where={"paper_id": paper_id})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])

        ids = [f"{paper_id}__{i}" for i in range(len(chunks))]
        metadatas = [
            {"paper_id": paper_id, "chunk_index": i} for i in range(len(chunks))
        ]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        logger.info(
            f"Stored {len(chunks)} chunks for paper {paper_id} in ChromaDB."
        )
        return len(chunks)

    def delete_paper_chunks(self, paper_id: str) -> None:
        """Remove all stored chunks for a given paper."""
        collection = self._get_collection()
        existing = collection.get(where={"paper_id": paper_id})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
            logger.info(
                f"Deleted {len(existing['ids'])} chunks for paper {paper_id}."
            )

    # ── Read ───────────────────────────────────────────────────────────────

    def search(
        self,
        query_embedding: List[float],
        paper_ids: List[str],
        top_k: int = 5,
    ) -> List[Dict]:
        """Find the top_k most similar chunks from the given paper_ids."""
        if not paper_ids:
            return []

        collection = self._get_collection()
        total = collection.count()
        if total == 0:
            return []

        n_results = min(top_k, total)

        try:
            if len(paper_ids) == 1:
                where_filter = {"paper_id": paper_ids[0]}
            else:
                where_filter = {"paper_id": {"$in": paper_ids}}

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.warning(f"ChromaDB query failed: {e}")
            return []

        output: List[Dict] = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                output.append(
                    {
                        "chunk_id": chunk_id,
                        "chunk_text": results["documents"][0][i],
                        "paper_id": results["metadatas"][0][i]["paper_id"],
                        "similarity": round(
                            1.0 - float(results["distances"][0][i]), 4
                        ),
                    }
                )
        return output

    def get_chunk_count(self, paper_id: str) -> int:
        """Return how many chunks are stored for a paper in ChromaDB."""
        try:
            collection = self._get_collection()
            existing = collection.get(where={"paper_id": paper_id})
            return len(existing["ids"])
        except Exception:
            return 0

    def has_embeddings(self, paper_id: str) -> bool:
        """Check whether embeddings exist for a paper."""
        return self.get_chunk_count(paper_id) > 0


chroma_service = ChromaService()
