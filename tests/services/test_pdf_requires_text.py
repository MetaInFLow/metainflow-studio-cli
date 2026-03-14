from pathlib import Path

import pytest

from metainflow_studio_cli.core.errors import ProcessingError
from metainflow_studio_cli.services.doc_parse.service import parse_document


def test_pdf_raises_when_no_text_and_no_ocr(monkeypatch, tmp_path: Path) -> None:
    pdf_file = tmp_path / "empty.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr("metainflow_studio_cli.services.doc_parse.parsers.parse_pdf", lambda _path: "")
    monkeypatch.setattr("metainflow_studio_cli.services.doc_parse.service.run_pdf_ocr", lambda _path, _lang: "")

    with pytest.raises(ProcessingError):
        parse_document(str(pdf_file), output="json")
