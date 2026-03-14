from __future__ import annotations

import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

from metainflow_studio_cli.core.errors import ProcessingError


def _is_readable_output(path: Path) -> bool:
    if not path.exists():
        return False

    if path.suffix in {".docx", ".xlsx"}:
        try:
            with zipfile.ZipFile(path):
                return True
        except zipfile.BadZipFile:
            return False

    return True


def _wait_for_output(path: Path, timeout_seconds: float = 2.0, interval_seconds: float = 0.1) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _is_readable_output(path):
            return True
        time.sleep(interval_seconds)
    return _is_readable_output(path)


def _run_soffice(command: list[str], source_label: str, target_label: str) -> None:
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=120)
    except FileNotFoundError as exc:
        raise ProcessingError(f"soffice not found; install LibreOffice to parse {source_label} files") from exc
    except subprocess.TimeoutExpired as exc:
        raise ProcessingError(f"{source_label} conversion timed out") from exc

    if completed.returncode != 0:
        raise ProcessingError(f"failed to convert {source_label} to {target_label}")


def _convert_with_soffice(path: Path, target_format: str, source_label: str, target_label: str) -> Path:
    output_dir = Path(tempfile.mkdtemp(prefix="metainflow_doc_convert_"))
    command = [
        "soffice",
        "--headless",
        "--convert-to",
        target_format,
        "--outdir",
        str(output_dir),
        str(path),
    ]

    converted = output_dir / f"{path.stem}.{target_format}"
    _run_soffice(command, source_label, target_label)
    if not _wait_for_output(converted):
        _run_soffice(command, source_label, target_label)

    if not _wait_for_output(converted):
        raise ProcessingError(f"{source_label[1:]} conversion completed but {target_label} output is missing")

    return converted


def convert_doc_to_docx(path: Path) -> Path:
    return _convert_with_soffice(path, "docx", ".doc", ".docx")


def convert_xls_to_xlsx(path: Path) -> Path:
    return _convert_with_soffice(path, "xlsx", ".xls", ".xlsx")
