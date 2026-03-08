"""
chunking.py – Split long documents into overlapping text chunks.
Chunks are ~500 words (≈ 375 tokens with 75 % token-to-word ratio).
"""
import re
from typing import List


class TextChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Args:
            chunk_size: Target chunk size in *words*.
            overlap:    Number of words to carry over into the next chunk.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    # ── Public ─────────────────────────────────────────────────────────────
    def chunk_text(self, text: str) -> List[str]:
        """Return a list of overlapping text chunks."""
        text = self._clean_text(text)
        if not text:
            return []

        sentences = self._split_sentences(text)
        if not sentences:
            return []

        chunks: List[str] = []
        current: List[str] = []
        current_words = 0

        for sent in sentences:
            sent_words = len(sent.split())

            if current_words + sent_words > self.chunk_size and current:
                chunks.append(" ".join(current).strip())

                # Carry overlap forward
                overlap_sents: List[str] = []
                overlap_words = 0
                for s in reversed(current):
                    w = len(s.split())
                    if overlap_words + w <= self.overlap:
                        overlap_sents.insert(0, s)
                        overlap_words += w
                    else:
                        break

                current = overlap_sents
                current_words = overlap_words

            current.append(sent)
            current_words += sent_words

        if current:
            chunks.append(" ".join(current).strip())

        return [c for c in chunks if len(c) > 50]

    # ── Helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = text.replace("\f", " ").replace("\x00", "")
        return text.strip()

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        # Split on '. ' or '? ' or '! ' followed by a capital letter
        pattern = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
        sents = pattern.split(text)
        sents = [s.strip() for s in sents if len(s.strip()) > 20]

        # Fallback: chunk by words if no sentence boundaries found
        if not sents:
            words = text.split()
            sents = [
                " ".join(words[i : i + 50]) for i in range(0, len(words), 50)
            ]
        return sents


text_chunker = TextChunker()
