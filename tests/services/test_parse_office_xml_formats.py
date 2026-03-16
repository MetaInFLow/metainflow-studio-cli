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


def test_parse_xlsx_preserves_sparse_columns(tmp_path: Path) -> None:
    file_path = tmp_path / "sparse.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>left</t></is></c><c r="C1" t="inlineStr"><is><t>right</t></is></c></row></sheetData></worksheet>""",
        )

    result = parse_document(str(file_path), output="json")

    assert result["success"] is True
    assert result["data"]["tables"] == [["left", "", "right"]]
    assert "| left |  | right |" in result["data"]["markdown"]


def test_parse_xlsx_expands_merged_cells(tmp_path: Path) -> None:
    file_path = tmp_path / "merged.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/sharedStrings.xml",
            """<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>region</t></si><si><t>total</t></si><si><t>north</t></si></sst>""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="C1" t="s"><v>1</v></c></row><row r="2"><c r="A2" t="s"><v>2</v></c></row><row r="3"></row></sheetData><mergeCells count="2"><mergeCell ref="A1:B1"/><mergeCell ref="A2:A3"/></mergeCells></worksheet>""",
        )

    result = parse_document(str(file_path), output="json")

    assert result["success"] is True
    assert result["data"]["tables"] == [
        ["region", "region", "total"],
        ["north", "", ""],
        ["north", "", ""],
    ]
    assert "| region | region | total |" in result["data"]["markdown"]
    assert "| north |  |  |" in result["data"]["markdown"]


def test_parse_xlsx_handles_cells_without_explicit_references(tmp_path: Path) -> None:
    file_path = tmp_path / "implicit-refs.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/sharedStrings.xml",
            """<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>name</t></si><si><t>role</t></si><si><t>alice</t></si><si><t>admin</t></si></sst>""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c t="s"><v>0</v></c><c t="s"><v>1</v></c></row><row><c t="s"><v>2</v></c><c t="s"><v>3</v></c></row></sheetData></worksheet>""",
        )

    result = parse_document(str(file_path), output="json")

    assert result["success"] is True
    assert result["data"]["tables"] == [["name", "role"], ["alice", "admin"]]


def test_parse_xlsx_rejects_unbounded_sparse_grid(tmp_path: Path) -> None:
    file_path = tmp_path / "oversized.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>ok</t></is></c><c r="ZZZ1" t="inlineStr"><is><t>boom</t></is></c></row></sheetData></worksheet>""",
        )

    with pytest.raises(ProcessingError, match="xlsx worksheet is too sparse to render safely"):
        parse_document(str(file_path), output="json")


def test_parse_xlsx_allows_large_dense_grid(tmp_path: Path) -> None:
    file_path = tmp_path / "dense.xlsx"
    row_xml = []
    for row_idx in range(1, 102):
        cells = []
        for col_idx in range(100):
            column_letter = chr(ord("A") + col_idx % 26)
            if col_idx >= 26:
                column_letter = chr(ord("A") + (col_idx // 26) - 1) + column_letter
            cell_ref = f"{column_letter}{row_idx}"
            cells.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{row_idx}-{col_idx}</t></is></c>')
        row_xml.append(f'<row r="{row_idx}">{"".join(cells)}</row>')

    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(row_xml)}</sheetData></worksheet>',
        )

    result = parse_document(str(file_path), output="json")

    assert result["success"] is True
    assert result["data"]["tables"][0][0] == "1-0"
    assert result["data"]["tables"][100][99] == "101-99"


def test_parse_xlsx_trims_leading_empty_rows(tmp_path: Path) -> None:
    file_path = tmp_path / "leading-empty-rows.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="3"><c r="A3" t="inlineStr"><is><t>value</t></is></c></row></sheetData></worksheet>""",
        )

    result = parse_document(str(file_path), output="json")

    assert result["success"] is True
    assert result["data"]["tables"] == [["value"]]


def test_parse_xlsx_allows_large_merged_header_block(tmp_path: Path) -> None:
    file_path = tmp_path / "merged-header.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>title</t></is></c></row></sheetData><mergeCells count="1"><mergeCell ref="A1:CW100"/></mergeCells></worksheet>""",
        )

    result = parse_document(str(file_path), output="json")

    assert result["success"] is True
    assert result["data"]["tables"][0][0] == "title"
    assert result["data"]["tables"][99][100] == "title"


def test_parse_xlsx_allows_high_offset_compact_data(tmp_path: Path) -> None:
    file_path = tmp_path / "offset.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="10001"><c r="Z10001" t="inlineStr"><is><t>value</t></is></c></row></sheetData></worksheet>""",
        )

    result = parse_document(str(file_path), output="json")

    assert result["success"] is True
    assert result["data"]["tables"] == [["value"]]


def test_parse_xlsx_rejects_huge_merged_ranges(tmp_path: Path) -> None:
    file_path = tmp_path / "huge-merge.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>title</t></is></c></row></sheetData><mergeCells count="1"><mergeCell ref="A1:ZZ1000"/></mergeCells></worksheet>""",
        )

    with pytest.raises(ProcessingError, match="xlsx worksheet is too large to render safely"):
        parse_document(str(file_path), output="json")


def test_parse_xlsx_splits_disconnected_regions(tmp_path: Path) -> None:
    file_path = tmp_path / "regions.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>name</t></is></c><c r="B1" t="inlineStr"><is><t>score</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>alice</t></is></c><c r="B2" t="inlineStr"><is><t>98</t></is></c></row><row r="6"><c r="F6" t="inlineStr"><is><t>region</t></is></c><c r="G6" t="inlineStr"><is><t>value</t></is></c></row><row r="7"><c r="F7" t="inlineStr"><is><t>north</t></is></c><c r="G7" t="inlineStr"><is><t>42</t></is></c></row></sheetData></worksheet>""",
        )

    result = parse_document(str(file_path), output="json")

    assert result["success"] is True
    assert result["data"]["tables"] == [
        ["name", "score"],
        ["alice", "98"],
        ["region", "value"],
        ["north", "42"],
    ]
    assert "| name | score |" in result["data"]["markdown"]
    assert "| region | value |" in result["data"]["markdown"]


def test_parse_xlsx_keeps_merged_block_together_when_splitting_regions(tmp_path: Path) -> None:
    file_path = tmp_path / "merged-regions.xlsx"
    with zipfile.ZipFile(file_path, "w") as archive:
        archive.writestr(
            "xl/sharedStrings.xml",
            """<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>region</t></si><si><t>total</t></si><si><t>north</t></si><si><t>meta</t></si><si><t>value</t></si></sst>""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="C1" t="s"><v>1</v></c></row><row r="2"><c r="A2" t="s"><v>2</v></c></row><row r="6"><c r="F6" t="s"><v>3</v></c><c r="G6" t="s"><v>4</v></c></row></sheetData><mergeCells count="2"><mergeCell ref="A1:B1"/><mergeCell ref="A2:A3"/></mergeCells></worksheet>""",
        )

    result = parse_document(str(file_path), output="json")

    assert result["success"] is True
    assert result["data"]["tables"] == [
        ["region", "region", "total"],
        ["north", "", ""],
        ["north", "", ""],
        ["meta", "value"],
    ]


@pytest.mark.parametrize("extension", [".docx", ".pptx", ".xlsx"])
def test_parse_invalid_office_file_raises_processing_error(tmp_path: Path, extension: str) -> None:
    file_path = tmp_path / f"broken{extension}"
    file_path.write_bytes(b"not a valid office zip")

    with pytest.raises(ProcessingError):
        parse_document(str(file_path), output="json")
