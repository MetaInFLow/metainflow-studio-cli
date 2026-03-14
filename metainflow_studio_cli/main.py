from __future__ import annotations

import json
from typing import NoReturn

import typer

from metainflow_studio_cli.core.errors import ExternalError, MetainflowError, ProcessingError, ValidationError
from metainflow_studio_cli.services.doc_parse.service import parse_document


app = typer.Typer(help="Metainflow studio CLI")


@app.callback()
def root() -> None:
    """Metainflow command group entrypoint."""


@app.command("parse-doc")
def parse_doc(file: str = typer.Option(..., "--file"), output: str = typer.Option("text", "--output")) -> None:
    envelope: dict | None = None
    try:
        envelope = parse_document(file_or_url=file, output=output)
    except ValidationError as exc:
        _emit_error(output, 2, str(exc), retryable=False)
    except ProcessingError as exc:
        _emit_error(output, 1, str(exc), retryable=False)
    except ExternalError as exc:
        _emit_error(output, 3, str(exc), retryable=True)
    except MetainflowError as exc:
        _emit_error(output, 1, str(exc), retryable=False)

    if envelope is None:
        _emit_error(output, 1, "unknown error", retryable=False)

    if output == "json":
        typer.echo(json.dumps(envelope, ensure_ascii=False))
    else:
        typer.echo(envelope["data"]["markdown"])


def _emit_error(output: str, code: int, message: str, retryable: bool) -> NoReturn:
    if output == "json":
        payload = {
            "success": False,
            "data": None,
            "meta": {"parser": "", "latency_ms": 0, "request_id": ""},
            "error": {"code": code, "message": message, "retryable": retryable},
        }
        typer.echo(json.dumps(payload, ensure_ascii=False))
    else:
        typer.echo(f"error: {message}", err=True)
    raise typer.Exit(code=code)


if __name__ == "__main__":
    app()
