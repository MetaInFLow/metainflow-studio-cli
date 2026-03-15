from pathlib import Path


SUPPORTED_EXTENSIONS = {
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


def detect_extension(file_value: str) -> str:
    return Path(file_value).suffix.lower()
