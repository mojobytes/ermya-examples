from unittest.mock import MagicMock
import pytest
from pdf_extractor import extract_text, PdfExtractionError


def test_extract_text_delegates_to_reader():
    fake_doc = MagicMock()
    fake_doc.extract_text.return_value = "EU AI Act Article 1 ..."
    fake_reader = MagicMock(return_value=fake_doc)

    text = extract_text("data/eu_ai_act.pdf", reader=fake_reader)

    fake_reader.assert_called_once_with("data/eu_ai_act.pdf")
    assert text == "EU AI Act Article 1 ..."


def test_extract_text_wraps_reader_failure():
    def boom(_path):
        raise RuntimeError("corrupt xref")
    with pytest.raises(PdfExtractionError) as exc:
        extract_text("data/broken.pdf", reader=boom)
    assert exc.value.path == "data/broken.pdf"
