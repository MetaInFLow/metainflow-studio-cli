from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from metainflow_studio_cli.core.errors import ProcessingError


MAX_XLSX_RENDER_CELLS = 50_000
MAX_XLSX_SPARSE_WINDOW = 10_000


def parse_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_csv(path: Path) -> tuple[str, list[list[str]]]:
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            rows.append([str(cell) for cell in row])

    if not rows:
        return "", []

    header = "| " + " | ".join(rows[0]) + " |"
    separator = "| " + " | ".join(["---"] * len(rows[0])) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows[1:]]
    markdown = "\n".join([header, separator, *body])
    return markdown, rows


def parse_html(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _read_xml_texts(xml_bytes: bytes) -> str:
    root = ET.fromstring(xml_bytes)
    texts = [elem.text for elem in root.iter() if elem.text and elem.text.strip()]
    return "\n".join(texts)


def _column_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha()).upper()
    if not letters:
        return 0

    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter) - ord("A") + 1)
    return index - 1


def _row_index(cell_ref: str) -> int:
    digits = "".join(ch for ch in cell_ref if ch.isdigit())
    if not digits:
        return 0
    return max(int(digits) - 1, 0)


def _cell_value(cell: ET.Element, shared: list[str]) -> str:
    value = ""
    value_elem = next((child for child in cell if child.tag.endswith("}v")), None)
    if value_elem is not None and value_elem.text is not None:
        value = value_elem.text

    cell_type = cell.attrib.get("t")
    if cell_type == "s" and value.isdigit():
        idx = int(value)
        return shared[idx] if 0 <= idx < len(shared) else ""

    if cell_type == "inlineStr":
        inline_texts = [elem.text or "" for elem in cell.iter() if elem.tag.endswith("}t")]
        return "".join(inline_texts)

    return value


def _parse_merge_range(cell_range: str) -> tuple[int, int, int, int]:
    start_ref, end_ref = cell_range.split(":", 1)
    start_row = _row_index(start_ref)
    end_row = _row_index(end_ref)
    start_col = _column_index(start_ref)
    end_col = _column_index(end_ref)
    return start_row, end_row, start_col, end_col


def _render_markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""

    header = "| " + " | ".join(rows[0]) + " |"
    separator = "| " + " | ".join(["---"] * len(rows[0])) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows[1:]]
    return "\n".join([header, separator, *body])


def _is_non_empty(value: str) -> bool:
    return bool(value and value.strip())


def _split_table_regions(cells: dict[tuple[int, int], str]) -> list[list[list[str]]]:
    non_empty = {coord for coord, value in cells.items() if _is_non_empty(value)}
    if not non_empty:
        return []

    rows: dict[int, list[int]] = {}
    for row_idx, col_idx in sorted(non_empty):
        rows.setdefault(row_idx, []).append(col_idx)

    segments: list[tuple[int, int, int]] = []
    for row_idx, cols in rows.items():
        start_col = cols[0]
        end_col = cols[0]
        for col_idx in cols[1:]:
            if col_idx - end_col <= 2:
                end_col = col_idx
                continue
            segments.append((row_idx, start_col, end_col))
            start_col = col_idx
            end_col = col_idx
        segments.append((row_idx, start_col, end_col))

    regions: list[list[tuple[int, int, int]]] = []
    visited: set[tuple[int, int, int]] = set()
    for start in sorted(segments):
        if start in visited:
            continue

        stack = [start]
        region: list[tuple[int, int, int]] = []
        visited.add(start)
        while stack:
            row_idx, start_col, end_col = stack.pop()
            region.append((row_idx, start_col, end_col))
            for neighbor in segments:
                if neighbor in visited:
                    continue
                neighbor_row, neighbor_start, neighbor_end = neighbor
                if abs(neighbor_row - row_idx) != 1:
                    continue
                overlaps = not (neighbor_end < start_col or end_col < neighbor_start)
                touches = neighbor_end + 1 == start_col or end_col + 1 == neighbor_start
                if overlaps or touches:
                    visited.add(neighbor)
                    stack.append(neighbor)

        regions.append(sorted(region))

    tables: list[list[list[str]]] = []
    for region in regions:
        min_row = min(row_idx for row_idx, _, _ in region)
        max_row = max(row_idx for row_idx, _, _ in region)
        min_col = min(start_col for _, start_col, _ in region)
        max_col = max(end_col for _, _, end_col in region)
        tables.append(
            [
                [cells.get((row_idx, col_idx), "") for col_idx in range(min_col, max_col + 1)]
                for row_idx in range(min_row, max_row + 1)
            ]
        )

    return tables


def _ensure_renderable_grid(
    min_row: int | None,
    min_col: int | None,
    max_row: int,
    max_col: int,
    populated_cells: int,
) -> None:
    if min_row is None or min_col is None or max_row < 0 or max_col < 0:
        return

    area = (max_row - min_row + 1) * (max_col - min_col + 1)
    if area > MAX_XLSX_RENDER_CELLS:
        raise ProcessingError("xlsx worksheet is too large to render safely")

    if area > MAX_XLSX_SPARSE_WINDOW and area > max(populated_cells, 1) * 10:
        raise ProcessingError("xlsx worksheet is too sparse to render safely")


def parse_docx(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            xml_bytes = archive.read("word/document.xml")
            return _read_xml_texts(xml_bytes)
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise ProcessingError(f"invalid docx file: {path.name}") from exc


def parse_pptx(path: Path) -> str:
    texts: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                    texts.append(_read_xml_texts(archive.read(name)))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise ProcessingError(f"invalid pptx file: {path.name}") from exc
    if not any(text.strip() for text in texts):
        raise ProcessingError(f"pptx file has no readable slide text: {path.name}")
    return "\n".join([t for t in texts if t.strip()])


def parse_xlsx(path: Path) -> tuple[str, list[list[str]]]:
    try:
        with zipfile.ZipFile(path) as archive:
            shared: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                shared = [elem.text or "" for elem in shared_root.iter() if elem.tag.endswith("}t")]

            sheet_tables: list[list[list[str]]] = []
            for name in archive.namelist():
                if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                    root = ET.fromstring(archive.read(name))
                    cells: dict[tuple[int, int], str] = {}
                    min_row: int | None = None
                    min_col: int | None = None
                    max_row = -1
                    max_col = -1
                    next_row_idx = 0

                    for row in root.iter():
                        if not row.tag.endswith("}row"):
                            continue
                        row_ref = row.attrib.get("r", "")
                        row_idx = _row_index(row_ref) if row_ref else next_row_idx
                        next_col_idx = 0
                        for cell in row:
                            if not cell.tag.endswith("}c"):
                                continue
                            cell_ref = cell.attrib.get("r", "")
                            col_idx = _column_index(cell_ref) if cell_ref else next_col_idx
                            cells[(row_idx, col_idx)] = _cell_value(cell, shared)
                            min_row = row_idx if min_row is None else min(min_row, row_idx)
                            min_col = col_idx if min_col is None else min(min_col, col_idx)
                            max_row = max(max_row, row_idx)
                            max_col = max(max_col, col_idx)
                            _ensure_renderable_grid(min_row, min_col, max_row, max_col, len(cells))
                            next_col_idx = col_idx + 1
                        next_row_idx = row_idx + 1

                    for merge in root.iter():
                        if not merge.tag.endswith("}mergeCell"):
                            continue
                        merge_ref = merge.attrib.get("ref")
                        if not merge_ref or ":" not in merge_ref:
                            continue
                        start_row, end_row, start_col, end_col = _parse_merge_range(merge_ref)
                        fill_value = cells.get((start_row, start_col), "")
                        min_row = start_row if min_row is None else min(min_row, start_row)
                        min_col = start_col if min_col is None else min(min_col, start_col)
                        max_row = max(max_row, end_row)
                        max_col = max(max_col, end_col)
                        merge_area = (end_row - start_row + 1) * (end_col - start_col + 1)
                        estimated_populated = len(cells) + max(merge_area - 1, 0)
                        _ensure_renderable_grid(min_row, min_col, max_row, max_col, estimated_populated)
                        for row_idx in range(start_row, end_row + 1):
                            for col_idx in range(start_col, end_col + 1):
                                cells[(row_idx, col_idx)] = fill_value

                    if min_row is not None and min_col is not None and max_row >= 0 and max_col >= 0:
                        sheet_tables.extend(_split_table_regions(cells))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise ProcessingError(f"invalid xlsx file: {path.name}") from exc

    tables = [row for table in sheet_tables for row in table]
    if not tables:
        raise ProcessingError(f"xlsx file has no readable worksheet data: {path.name}")

    markdown = "\n\n".join(_render_markdown_table(table) for table in sheet_tables if table)
    return markdown, tables


def parse_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception:  # noqa: BLE001
        return ""

    try:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join([text for text in pages if text.strip()])
    except Exception:  # noqa: BLE001
        return ""
