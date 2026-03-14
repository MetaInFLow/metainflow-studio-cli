from __future__ import annotations

from pathlib import Path


REQUIRED_SAMPLE_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".pptx",
    ".xls",
    ".xlsx",
    ".csv",
    ".txt",
    ".md",
    ".html",
}


def summarize_sample_matrix(samples_dir: Path) -> dict[str, list[str]]:
    present_extensions = {path.suffix.lower() for path in samples_dir.rglob("*") if path.is_file()}
    present_required = sorted(ext for ext in present_extensions if ext in REQUIRED_SAMPLE_EXTENSIONS)
    missing = sorted(REQUIRED_SAMPLE_EXTENSIONS - set(present_required))

    return {
        "required_extensions": sorted(REQUIRED_SAMPLE_EXTENSIONS),
        "present_extensions": present_required,
        "missing_extensions": missing,
    }
