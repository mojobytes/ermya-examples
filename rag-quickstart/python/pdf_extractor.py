"""Extract text from PDF documents via oxidize-pdf.

The reader is injectable so tests never open a real PDF. main() uses the real
oxidize_pdf.PdfReader.open.

``extract_rag_chunks`` uses oxidize-pdf's RAG-oriented chunking
(``rag_chunks()``): semantic chunks that respect headings/sections, each
carrying its heading context and page numbers, mapped into the example's own
``PdfChunk`` so the pipeline never depends on the engine's native chunk type.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PdfChunk:
    """A RAG-ready chunk: text plus where it lives in the document."""

    text: str
    heading: str
    pages: tuple[int, ...]


class PdfExtractionError(Exception):
    """Raised when a PDF cannot be read/extracted."""

    def __init__(self, path: str, cause: Exception):
        super().__init__(f"failed to extract text from {path}: {cause}")
        self.path = path
        self.cause = cause


def _default_reader(path):
    from oxidize_pdf import PdfReader  # imported lazily for a clear error

    return PdfReader.open(path)


def extract_text(path: str | Path, *, reader=None) -> str:
    """Extract all text from the PDF at ``path``."""
    reader = reader or _default_reader
    key = str(path)
    try:
        document = reader(key)
        text = document.extract_text()
        if isinstance(text, list):
            # oxidize-pdf returns one string per page; join into a single text.
            text = "\n".join(text)
        return text
    except Exception as cause:  # noqa: BLE001 — wrap any engine error
        raise PdfExtractionError(key, cause) from cause


def extract_rag_chunks(path: str | Path, *, reader=None) -> list[PdfChunk]:
    """RAG-oriented extraction: semantic chunks with heading + page context.

    Delegates to oxidize-pdf's ``rag_chunks()`` (default configuration) and
    maps each engine chunk into a ``PdfChunk``.
    """
    reader = reader or _default_reader
    key = str(path)
    try:
        document = reader(key)
        return [
            PdfChunk(
                text=chunk.text,
                # chunks outside any heading carry heading_context = None
                heading=chunk.heading_context or "",
                pages=tuple(chunk.page_numbers),
            )
            for chunk in document.rag_chunks()
        ]
    except Exception as cause:  # noqa: BLE001 — wrap any engine error
        raise PdfExtractionError(key, cause) from cause
