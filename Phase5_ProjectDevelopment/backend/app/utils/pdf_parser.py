"""
pdf_parser.py – Extract text from PDF files / URLs using PyMuPDF (fitz).
"""
import os
import tempfile
from typing import Optional

import requests
import fitz  # PyMuPDF


class PDFParser:
    """Download and extract plain text from PDF documents."""

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (ResearchHub AI; research-tool) "
            "AppleWebKit/537.36 (KHTML, like Gecko)"
        )
    }

    # ── Public API ─────────────────────────────────────────────────────────
    def extract_text_from_url(self, pdf_url: str) -> Optional[str]:
        """Download a PDF from *pdf_url* and return its text content."""
        try:
            response = requests.get(
                pdf_url, headers=self._HEADERS, timeout=60, stream=True
            )
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                for chunk in response.iter_content(chunk_size=8_192):
                    tmp.write(chunk)
                tmp_path = tmp.name

            try:
                return self.extract_text_from_file(tmp_path)
            finally:
                os.unlink(tmp_path)

        except Exception as exc:
            print(f"[PDFParser] Error fetching {pdf_url}: {exc}")
            return None

    def extract_text_from_file(self, file_path: str) -> Optional[str]:
        """Extract text from a local PDF file."""
        try:
            doc = fitz.open(file_path)
            pages = []
            for page in doc:
                text = page.get_text("text")
                if text.strip():
                    pages.append(text)
            doc.close()
            return "\n".join(pages) if pages else None
        except Exception as exc:
            print(f"[PDFParser] Error reading file {file_path}: {exc}")
            return None

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> Optional[str]:
        """Extract text from raw PDF bytes."""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages = []
            for page in doc:
                text = page.get_text("text")
                if text.strip():
                    pages.append(text)
            doc.close()
            return "\n".join(pages) if pages else None
        except Exception as exc:
            print(f"[PDFParser] Error reading bytes: {exc}")
            return None


pdf_parser = PDFParser()
