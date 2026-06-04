"""Deterministic text chunking and markdown document parsing.

Pure functions, no I/O dependencies beyond reading files from a directory.
Chunking is character-based and deterministic so the RAG pipeline is
reproducible.
"""

from __future__ import annotations

from pathlib import Path


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text into overlapping windows of ``chunk_size`` characters.

    Each window starts ``chunk_size - chunk_overlap`` characters after the
    previous one. A degenerate overlap (>= chunk_size) is clamped so the step
    is at least 1 and the function always terminates.
    """
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    step = max(1, chunk_size - chunk_overlap)
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        if start + chunk_size >= len(text):
            break
        start += step
    return chunks


def parse_markdown_files(data_dir: Path) -> list[str]:
    """Read every ``*.md`` file in ``data_dir`` (sorted) and return their text."""
    directory = Path(data_dir)
    return [path.read_text() for path in sorted(directory.glob("*.md"))]
