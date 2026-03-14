from pathlib import Path

from metainflow_studio_cli.services.doc_parse.service import parse_document


def test_pdf_runs_ocr_when_text_is_empty(monkeypatch, tmp_path: Path) -> None:
    pdf_file = tmp_path / "scan.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        "metainflow_studio_cli.services.doc_parse.parsers.parse_pdf",
        lambda _path: "",
    )
    monkeypatch.setattr(
        "metainflow_studio_cli.services.doc_parse.service.run_pdf_ocr",
        lambda _path, _lang: "ocr fallback text",
    )

    result = parse_document(str(pdf_file), output="json")

    assert result["success"] is True
    assert "ocr fallback text" in result["data"]["markdown"]
