from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from metainflow_studio_cli.core.errors import ProcessingError
from metainflow_studio_cli.services.doc_parse.service import parse_document


def test_parse_minimal_docx(tmp_path: Path) -> None:
    file_path = tmp_path / "demo.docx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            """<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>Hello Docx</w:t></w:r></w:p></w:body></w:document>""",
        )

    result = parse_document(str(file_path), output="json")
    assert result["success"] is True
    assert "Hello Docx" in result["data"]["markdown"]


def test_parse_minimal_pptx(tmp_path: Path) -> None:
    file_path = tmp_path / "slides.pptx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "ppt/slides/slide1.xml",
            """<p:sld xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\" xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\"><p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Hello Pptx</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>""",
        )

    result = parse_document(str(file_path), output="json")
    assert result["success"] is True
    assert "Hello Pptx" in result["data"]["markdown"]


def test_parse_minimal_xlsx(tmp_path: Path) -> None:
    file_path = tmp_path / "sheet.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/sharedStrings.xml",
            """<sst xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><si><t>name</t></si><si><t>value</t></si><si><t>alice</t></si><si><t>42</t></si></sst>""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><sheetData><row r=\"1\"><c r=\"A1\" t=\"s\"><v>0</v></c><c r=\"B1\" t=\"s\"><v>1</v></c></row><row r=\"2\"><c r=\"A2\" t=\"s\"><v>2</v></c><c r=\"B2\" t=\"s\"><v>3</v></c></row></sheetData></worksheet>""",
        )

    result = parse_document(str(file_path), output="json")
    assert result["success"] is True
    assert "alice" in result["data"]["markdown"]


def test_parse_xlsx_inline_strings(tmp_path: Path) -> None:
    file_path = tmp_path / "inline.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>name</t></is></c><c r="B1" t="inlineStr"><is><t>role</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>alice</t></is></c><c r="B2" t="inlineStr"><is><t>admin</t></is></c></row></sheetData></worksheet>""",
        )

    result = parse_document(str(file_path), output="json")

    assert result["success"] is True
    assert "name" in result["data"]["markdown"]
    assert "admin" in result["data"]["markdown"]


@pytest.mark.parametrize("extension", [".docx", ".pptx", ".xlsx"])
def test_parse_invalid_office_file_raises_processing_error(tmp_path: Path, extension: str) -> None:
    file_path = tmp_path / f"broken{extension}"
    file_path.write_bytes(b"not a valid office zip")

    with pytest.raises(ProcessingError):
        parse_document(str(file_path), output="json")
