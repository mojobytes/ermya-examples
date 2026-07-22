"""Extract text from PDF documents via oxidize-pdf.

The reader is injectable so tests never open a real PDF. main() uses the real
oxidize_pdf.PdfReader.open.
"""
from __future__ import annotations

from pathlib import Path


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
        return document.extract_text()
    except Exception as cause:  # noqa: BLE001 — wrap any engine error
        raise PdfExtractionError(key, cause) from cause
