from pathlib import Path
import zipfile

from metainflow_studio_cli.services.doc_parse.service import parse_document


def test_doc_file_uses_converter(monkeypatch, tmp_path: Path) -> None:
    source_doc = tmp_path / "legacy.doc"
    source_doc.write_bytes(b"doc-binary")
    converted_docx = tmp_path / "legacy.docx"
    with zipfile.ZipFile(converted_docx, "w") as archive:
        archive.writestr(
            "word/document.xml",
            """<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>converted text</w:t></w:r></w:p></w:body></w:document>""",
        )

    called = {"value": False}

    def fake_convert_doc_to_docx(path: Path) -> Path:
        assert path == source_doc
        called["value"] = True
        return converted_docx

    monkeypatch.setattr(
        "metainflow_studio_cli.services.doc_parse.service.convert_doc_to_docx",
        fake_convert_doc_to_docx,
    )

    result = parse_document(str(source_doc), output="json")
    assert result["success"] is True
    assert called["value"] is True
    assert "converted text" in result["data"]["markdown"]
