import subprocess
from pathlib import Path
import zipfile

import pytest

from metainflow_studio_cli.core.errors import ProcessingError
from metainflow_studio_cli.services.doc_parse.converters import convert_xls_to_xlsx
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
    assert result["data"]["source"]["resolved_path"] == str(source_doc)
    assert result["data"]["source"]["file_type"] == ".doc"


def test_xls_file_uses_converter(monkeypatch, tmp_path: Path) -> None:
    source_xls = tmp_path / "legacy.xls"
    source_xls.write_bytes(b"xls-binary")
    converted_xlsx = tmp_path / "legacy.xlsx"
    with zipfile.ZipFile(converted_xlsx, "w") as archive:
        archive.writestr(
            "xl/sharedStrings.xml",
            """<sst xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><si><t>name</t></si><si><t>value</t></si><si><t>alice</t></si><si><t>42</t></si></sst>""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><sheetData><row r=\"1\"><c r=\"A1\" t=\"s\"><v>0</v></c><c r=\"B1\" t=\"s\"><v>1</v></c></row><row r=\"2\"><c r=\"A2\" t=\"s\"><v>2</v></c><c r=\"B2\" t=\"s\"><v>3</v></c></row></sheetData></worksheet>""",
        )

    called = {"value": False}

    def fake_convert_xls_to_xlsx(path: Path) -> Path:
        assert path == source_xls
        called["value"] = True
        return converted_xlsx

    monkeypatch.setattr(
        "metainflow_studio_cli.services.doc_parse.service.convert_xls_to_xlsx",
        fake_convert_xls_to_xlsx,
        raising=False,
    )

    result = parse_document(str(source_xls), output="json")
    assert result["success"] is True
    assert called["value"] is True
    assert "alice" in result["data"]["markdown"]
    assert result["data"]["source"]["resolved_path"] == str(source_xls)
    assert result["data"]["source"]["file_type"] == ".xls"


def test_convert_xls_to_xlsx_requires_soffice(monkeypatch, tmp_path: Path) -> None:
    source_xls = tmp_path / "legacy.xls"
    source_xls.write_bytes(b"xls-binary")

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(ProcessingError, match="soffice not found; install LibreOffice to parse .xls files"):
        convert_xls_to_xlsx(source_xls)


def test_convert_xls_to_xlsx_requires_output_file(monkeypatch, tmp_path: Path) -> None:
    source_xls = tmp_path / "legacy.xls"
    source_xls.write_bytes(b"xls-binary")
    output_dir = tmp_path / "converted"
    output_dir.mkdir()

    monkeypatch.setattr(
        "tempfile.mkdtemp",
        lambda prefix: str(output_dir),
    )
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=["soffice"], returncode=0),
    )

    with pytest.raises(ProcessingError, match="xls conversion completed but .xlsx output is missing"):
        convert_xls_to_xlsx(source_xls)
