from unittest.mock import MagicMock
import pytest
from pdf_extractor import (
    PdfChunk,
    PdfExtractionError,
    extract_rag_chunks,
    extract_text,
)


def test_extract_text_delegates_to_reader():
    fake_doc = MagicMock()
    fake_doc.extract_text.return_value = "EU AI Act Article 1 ..."
    fake_reader = MagicMock(return_value=fake_doc)

    text = extract_text("data/eu_ai_act.pdf", reader=fake_reader)

    fake_reader.assert_called_once_with("data/eu_ai_act.pdf")
    assert text == "EU AI Act Article 1 ..."


def test_extract_text_joins_per_page_list():
    # oxidize-pdf's extract_text() returns list[str] (one entry per page);
    # the extractor must join pages into a single string.
    fake_doc = MagicMock()
    fake_doc.extract_text.return_value = ["page one text", "page two text"]
    fake_reader = MagicMock(return_value=fake_doc)

    text = extract_text("data/eu_ai_act.pdf", reader=fake_reader)

    assert text == "page one text\npage two text"


def test_extract_text_wraps_reader_failure():
    def boom(_path):
        raise RuntimeError("corrupt xref")
    with pytest.raises(PdfExtractionError) as exc:
        extract_text("data/broken.pdf", reader=boom)
    assert exc.value.path == "data/broken.pdf"


def _fake_engine_chunk(text, heading, pages):
    chunk = MagicMock()
    chunk.text = text
    chunk.heading_context = heading
    chunk.page_numbers = pages
    return chunk


def test_extract_rag_chunks_maps_engine_chunks():
    fake_doc = MagicMock()
    fake_doc.rag_chunks.return_value = [
        _fake_engine_chunk("Article 1 ...", "Chapter I", [0, 1]),
        _fake_engine_chunk("Article 2 ...", "Chapter I > Scope", [1]),
    ]
    fake_reader = MagicMock(return_value=fake_doc)

    chunks = extract_rag_chunks("data/eu_ai_act.pdf", reader=fake_reader)

    fake_reader.assert_called_once_with("data/eu_ai_act.pdf")
    assert chunks == [
        PdfChunk(text="Article 1 ...", heading="Chapter I", pages=(0, 1)),
        PdfChunk(text="Article 2 ...", heading="Chapter I > Scope", pages=(1,)),
    ]


def test_extract_rag_chunks_normalizes_missing_heading():
    # engine chunks outside any heading have heading_context = None
    fake_doc = MagicMock()
    fake_doc.rag_chunks.return_value = [_fake_engine_chunk("preamble", None, [0])]
    chunks = extract_rag_chunks("data/x.pdf", reader=MagicMock(return_value=fake_doc))
    assert chunks[0].heading == ""


def test_extract_rag_chunks_wraps_engine_failure():
    def boom(_path):
        raise RuntimeError("corrupt xref")
    with pytest.raises(PdfExtractionError) as exc:
        extract_rag_chunks("data/broken.pdf", reader=boom)
    assert exc.value.path == "data/broken.pdf"
