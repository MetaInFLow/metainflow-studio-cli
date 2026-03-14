from __future__ import annotations

from pathlib import Path


def run_pdf_ocr(path: Path, lang: str = "chi_sim+eng") -> str:
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except Exception:  # noqa: BLE001
        return ""

    pages = convert_from_path(str(path))
    text_parts = [pytesseract.image_to_string(image, lang=lang) for image in pages]
    return "\n".join([chunk for chunk in text_parts if chunk.strip()])
