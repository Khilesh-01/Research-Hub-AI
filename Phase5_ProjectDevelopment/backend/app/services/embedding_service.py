"""
embedding_service.py – Generate sentence embeddings using Sentence Transformers.
Model: all-mpnet-base-v2  (768-dimensional embeddings)
Singleton pattern to avoid loading the model multiple times.
"""
from typing import List
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Lazy-loaded singleton wrapper around SentenceTransformer."""

    _instance: "EmbeddingService | None" = None
    _model = None
    MODEL_NAME = "all-mpnet-base-v2"    # 768-dim

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model: {self.MODEL_NAME}")
            self._model = SentenceTransformer(self.MODEL_NAME)
            logger.info("Model loaded successfully.")
        return self._model

    def generate_embedding(self, text: str) -> List[float]:
        """Return a 768-dimensional embedding vector for *text*."""
        model = self._get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Return embeddings for a list of texts (batched for efficiency)."""
        if not texts:
            return []
        model = self._get_model()
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        )
        return [e.tolist() for e in embeddings]


embedding_service = EmbeddingService()
