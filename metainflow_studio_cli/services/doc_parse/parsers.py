from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from metainflow_studio_cli.core.errors import ProcessingError


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
    tables: list[list[str]] = []
    markdown_lines: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            shared: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                shared = [elem.text or "" for elem in shared_root.iter() if elem.tag.endswith("}t")]

            for name in archive.namelist():
                if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                    root = ET.fromstring(archive.read(name))
                    for row in root.iter():
                        if not row.tag.endswith("}row"):
                            continue
                        values: list[str] = []
                        for cell in row:
                            if not cell.tag.endswith("}c"):
                                continue
                            value = ""
                            value_elem = next((c for c in cell if c.tag.endswith("}v")), None)
                            if value_elem is not None and value_elem.text is not None:
                                value = value_elem.text
                            cell_type = cell.attrib.get("t")
                            if cell_type == "s" and value.isdigit():
                                idx = int(value)
                                value = shared[idx] if 0 <= idx < len(shared) else ""
                            elif cell_type == "inlineStr":
                                inline_texts = [elem.text or "" for elem in cell.iter() if elem.tag.endswith("}t")]
                                value = "".join(inline_texts)
                            values.append(value)
                        if values:
                            tables.append(values)
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise ProcessingError(f"invalid xlsx file: {path.name}") from exc

    if not tables:
        raise ProcessingError(f"xlsx file has no readable worksheet data: {path.name}")

    if tables:
        markdown_lines.append("| " + " | ".join(tables[0]) + " |")
        markdown_lines.append("| " + " | ".join(["---"] * len(tables[0])) + " |")
        for row in tables[1:]:
            markdown_lines.append("| " + " | ".join(row) + " |")
    return "\n".join(markdown_lines), tables


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
