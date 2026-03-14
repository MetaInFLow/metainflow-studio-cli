from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

from metainflow_studio_cli.core.errors import ExternalError, ValidationError


@dataclass(slots=True)
class ResolvedInput:
    source_type: str
    local_path: Path
    source: str


def resolve_input(file_or_url: str, download_dir: Path | None = None, timeout_seconds: int = 30) -> ResolvedInput:
    parsed = urlparse(file_or_url)
    if parsed.scheme in {"http", "https"}:
        target_dir = download_dir or Path(tempfile.mkdtemp(prefix="metainflow_docparse_"))
        target_dir.mkdir(parents=True, exist_ok=True)

        suffix = Path(parsed.path).suffix.lower() or ".bin"
        output_file = target_dir / f"downloaded{suffix}"
        try:
            response = httpx.get(file_or_url, timeout=timeout_seconds)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise ExternalError(f"failed to download URL: {file_or_url}") from exc

        output_file.write_bytes(response.content)
        return ResolvedInput(source_type="url", local_path=output_file, source=file_or_url)

    path = Path(file_or_url).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise ValidationError(f"file not found: {path}")

    return ResolvedInput(source_type="local", local_path=path, source=file_or_url)
