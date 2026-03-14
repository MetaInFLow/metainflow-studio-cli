from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from metainflow_studio_cli.core.errors import ProcessingError


def convert_doc_to_docx(path: Path) -> Path:
    output_dir = Path(tempfile.mkdtemp(prefix="metainflow_doc_convert_"))
    command = [
        "soffice",
        "--headless",
        "--convert-to",
        "docx",
        "--outdir",
        str(output_dir),
        str(path),
    ]

    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=120)
    except FileNotFoundError as exc:
        raise ProcessingError("soffice not found; install LibreOffice to parse .doc files") from exc
    except subprocess.TimeoutExpired as exc:
        raise ProcessingError(".doc conversion timed out") from exc

    if completed.returncode != 0:
        raise ProcessingError("failed to convert .doc to .docx")

    converted = output_dir / f"{path.stem}.docx"
    if not converted.exists():
        raise ProcessingError("doc conversion completed but .docx output is missing")

    return converted
