from __future__ import annotations

import time
from pathlib import Path

from metainflow_studio_cli.core.errors import ProcessingError, ValidationError
from metainflow_studio_cli.services.doc_parse.converters import convert_doc_to_docx
from metainflow_studio_cli.services.doc_parse.detector import SUPPORTED_EXTENSIONS, detect_extension
from metainflow_studio_cli.services.doc_parse.input_resolver import resolve_input
from metainflow_studio_cli.services.doc_parse.ocr import run_pdf_ocr
from metainflow_studio_cli.services.doc_parse import parsers


def _extract_markdown(path: Path, extension: str) -> tuple[str, list[list[str]]]:
    if extension in {".txt", ".md"}:
        return parsers.parse_text(path), []

    if extension == ".csv":
        return parsers.parse_csv(path)

    if extension == ".html":
        return parsers.parse_html(path), []

    if extension == ".docx":
        return parsers.parse_docx(path), []

    if extension == ".pptx":
        return parsers.parse_pptx(path), []

    if extension == ".xlsx":
        return parsers.parse_xlsx(path)

    if extension == ".pdf":
        extracted = parsers.parse_pdf(path)
        if extracted.strip():
            return extracted, []
        ocr_text = run_pdf_ocr(path, "chi_sim+eng")
        if not ocr_text.strip():
            raise ProcessingError("pdf text extraction failed; install pypdf and OCR dependencies")
        return ocr_text, []

    raise ProcessingError(f"parser for {extension} is not implemented yet")


def parse_document(file_or_url: str, output: str = "text") -> dict:
    if output not in {"text", "json"}:
        raise ValidationError("--output must be one of: text, json")

    started = time.perf_counter()
    resolved = resolve_input(file_or_url)
    source_path = resolved.local_path
    extension = detect_extension(str(source_path))

    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValidationError(f"unsupported file type: {extension}; supported: {supported}")

    if extension == ".doc":
        source_path = convert_doc_to_docx(source_path)
        extension = ".docx"

    markdown, tables = _extract_markdown(source_path, extension)

    return {
        "success": True,
        "data": {
            "markdown": markdown,
            "blocks": [],
            "tables": tables,
            "source": {
                "input": file_or_url,
                "resolved_path": str(source_path),
                "file_type": extension,
            },
        },
        "meta": {
            "parser": "local",
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "request_id": "",
        },
        "error": None,
    }
