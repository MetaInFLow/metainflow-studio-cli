from __future__ import annotations

import json
import time
from typing import NoReturn

import typer

from metainflow_studio_cli.core.errors import ExternalError, MetainflowError, ProcessingError, ValidationError
from metainflow_studio_cli.services.doc_parse.service import parse_document
from metainflow_studio_cli.services.enterprise_query.service import enterprise_balance, enterprise_query, enterprise_search
from metainflow_studio_cli.services.web_fetch.service import web_crawl
from metainflow_studio_cli.services.web_search.service import search_summary


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


@app.command("search-summary")
def search_summary_command(
    query: str = typer.Option(..., "--query"),
    instruction: str = typer.Option("", "--instruction"),
    output: str = typer.Option("text", "--output", "-o"),
) -> None:
    started = time.perf_counter()
    envelope: dict | None = None
    try:
        envelope = search_summary(query=query, instruction=instruction, output=output)
    except ValidationError as exc:
        if output == "json":
            _emit_search_error(query, instruction, 2, str(exc), retryable=False, latency_ms=_elapsed_ms(started))
        _emit_error(output, 2, str(exc), retryable=False)
    except ProcessingError as exc:
        if output == "json":
            _emit_search_error(query, instruction, 1, str(exc), retryable=False, latency_ms=_elapsed_ms(started))
        _emit_error(output, 1, str(exc), retryable=False)
    except ExternalError as exc:
        if output == "json":
            _emit_search_error(query, instruction, 3, str(exc), retryable=True, latency_ms=_elapsed_ms(started))
        _emit_error(output, 3, str(exc), retryable=True)
    except MetainflowError as exc:
        if output == "json":
            _emit_search_error(query, instruction, 1, str(exc), retryable=False, latency_ms=_elapsed_ms(started))
        _emit_error(output, 1, str(exc), retryable=False)

    if envelope is None:
        _emit_error(output, 1, "unknown error", retryable=False)

    if output == "json":
        typer.echo(json.dumps(envelope, ensure_ascii=False))
        if envelope.get("success") is False and envelope.get("error"):
            raise typer.Exit(code=int(envelope["error"]["code"]))
    else:
        typer.echo(envelope["data"]["summary"])


@app.command("web-crawl")
def web_crawl_command(
    url: str = typer.Option(..., "--url"),
    instruction: str = typer.Option("", "--instruction"),
    output: str = typer.Option("text", "--output", "-o"),
) -> None:
    started = time.perf_counter()
    envelope: dict | None = None
    try:
        envelope = web_crawl(url=url, instruction=instruction, output=output)
    except ValidationError as exc:
        if output == "json":
            _emit_web_crawl_error(url, instruction, 2, str(exc), retryable=False, latency_ms=_elapsed_ms(started))
        _emit_error(output, 2, str(exc), retryable=False)
    except ProcessingError as exc:
        if output == "json":
            _emit_web_crawl_error(url, instruction, 1, str(exc), retryable=False, latency_ms=_elapsed_ms(started))
        _emit_error(output, 1, str(exc), retryable=False)
    except ExternalError as exc:
        if output == "json":
            _emit_web_crawl_error(url, instruction, 3, str(exc), retryable=True, latency_ms=_elapsed_ms(started))
        _emit_error(output, 3, str(exc), retryable=True)
    except MetainflowError as exc:
        if output == "json":
            _emit_web_crawl_error(url, instruction, 1, str(exc), retryable=False, latency_ms=_elapsed_ms(started))
        _emit_error(output, 1, str(exc), retryable=False)

    if envelope is None:
        _emit_error(output, 1, "unknown error", retryable=False)

    if output == "json":
        typer.echo(json.dumps(envelope, ensure_ascii=False))
        if envelope.get("success") is False and envelope.get("error"):
            raise typer.Exit(code=int(envelope["error"]["code"]))
    else:
        extracted = envelope["data"].get("extracted", "")
        if extracted:
            typer.echo(extracted)
        else:
            typer.echo(envelope["data"]["markdown"])


@app.command("enterprise-query")
def enterprise_query_command(
    query_type: str = typer.Option(..., "--type"),
    keyword: str = typer.Option(..., "--keyword"),
    session_id: str = typer.Option("", "--session-id"),
    skip: int = typer.Option(0, "--skip"),
    role_code: str = typer.Option("", "--role-code"),
    role_history: str = typer.Option("", "--role-history"),
    refresh: bool = typer.Option(False, "--refresh"),
    output: str = typer.Option("text", "--output", "-o"),
) -> None:
    envelope: dict | None = None
    try:
        envelope = enterprise_query(
            query_type=query_type,
            keyword=keyword,
            output=output,
            session_id=session_id,
            skip=skip,
            role_code=role_code,
            role_history=role_history,
            refresh=refresh,
        )
    except ValidationError as exc:
        _emit_enterprise_error("query", {"query_type": query_type.strip(), "keyword": keyword.strip()}, 2, str(exc), False, output)
    except ProcessingError as exc:
        _emit_enterprise_error("query", {"query_type": query_type.strip(), "keyword": keyword.strip()}, 1, str(exc), False, output)
    except ExternalError as exc:
        _emit_enterprise_error("query", {"query_type": query_type.strip(), "keyword": keyword.strip()}, 3, str(exc), True, output)
    except MetainflowError as exc:
        _emit_enterprise_error("query", {"query_type": query_type.strip(), "keyword": keyword.strip()}, 1, str(exc), False, output)

    if envelope is None:
        _emit_enterprise_error("query", {"query_type": query_type.strip(), "keyword": keyword.strip()}, 1, "unknown error", False, output)

    if output == "json":
        typer.echo(json.dumps(envelope, ensure_ascii=False))
    else:
        typer.echo(envelope["data"]["markdown"])


@app.command("enterprise-search")
def enterprise_search_command(
    keyword: str = typer.Option(..., "--keyword"),
    session_id: str = typer.Option("", "--session-id"),
    refresh: bool = typer.Option(False, "--refresh"),
    output: str = typer.Option("text", "--output", "-o"),
) -> None:
    envelope: dict | None = None
    try:
        envelope = enterprise_search(keyword=keyword, output=output, session_id=session_id, refresh=refresh)
    except ValidationError as exc:
        _emit_enterprise_error("search", {"keyword": keyword.strip()}, 2, str(exc), False, output)
    except ProcessingError as exc:
        _emit_enterprise_error("search", {"keyword": keyword.strip()}, 1, str(exc), False, output)
    except ExternalError as exc:
        _emit_enterprise_error("search", {"keyword": keyword.strip()}, 3, str(exc), True, output)
    except MetainflowError as exc:
        _emit_enterprise_error("search", {"keyword": keyword.strip()}, 1, str(exc), False, output)

    if envelope is None:
        _emit_enterprise_error("search", {"keyword": keyword.strip()}, 1, "unknown error", False, output)

    if output == "json":
        typer.echo(json.dumps(envelope, ensure_ascii=False))
    else:
        typer.echo(envelope["data"]["markdown"])


@app.command("enterprise-balance")
def enterprise_balance_command(
    session_id: str = typer.Option("", "--session-id"),
    refresh: bool = typer.Option(False, "--refresh"),
    output: str = typer.Option("text", "--output", "-o"),
) -> None:
    envelope: dict | None = None
    try:
        envelope = enterprise_balance(output=output, session_id=session_id, refresh=refresh)
    except ValidationError as exc:
        _emit_enterprise_error("balance", {}, 2, str(exc), False, output)
    except ProcessingError as exc:
        _emit_enterprise_error("balance", {}, 1, str(exc), False, output)
    except ExternalError as exc:
        _emit_enterprise_error("balance", {}, 3, str(exc), True, output)
    except MetainflowError as exc:
        _emit_enterprise_error("balance", {}, 1, str(exc), False, output)

    if envelope is None:
        _emit_enterprise_error("balance", {}, 1, "unknown error", False, output)

    if output == "json":
        typer.echo(json.dumps(envelope, ensure_ascii=False))
    else:
        typer.echo(envelope["data"]["markdown"])


def _emit_search_error(query: str, instruction: str, code: int, message: str, retryable: bool, latency_ms: int) -> NoReturn:
    payload = {
        "success": False,
        "data": {
            "summary": "",
            "query": query.strip(),
            "instruction": instruction.strip(),
            "results": [],
        },
        "meta": {
            "search_provider": "",
            "summary_provider": "",
            "model": "",
            "latency_ms": latency_ms,
            "request_id": "",
        },
        "error": {"code": code, "message": message, "retryable": retryable},
    }
    typer.echo(json.dumps(payload, ensure_ascii=False))
    raise typer.Exit(code=code)


def _emit_web_crawl_error(
    url: str,
    instruction: str,
    code: int,
    message: str,
    retryable: bool,
    latency_ms: int,
) -> NoReturn:
    payload = {
        "success": False,
        "data": {
            "markdown": "",
            "extracted": "",
            "url": url.strip(),
            "title": "",
            "instruction": instruction.strip(),
            "links": [],
        },
        "meta": {
            "fetch_provider": "",
            "summary_provider": "",
            "model": "",
            "latency_ms": latency_ms,
            "request_id": "",
        },
        "error": {"code": code, "message": message, "retryable": retryable},
    }
    typer.echo(json.dumps(payload, ensure_ascii=False))
    raise typer.Exit(code=code)


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _emit_enterprise_error(kind: str, data: dict[str, object], code: int, message: str, retryable: bool, output: str) -> NoReturn:
    if output == "json":
        payload = {
            "success": False,
            "data": {"kind": kind, **data},
            "meta": {
                "provider": "yuanjian",
                "endpoint": "",
                "latency_ms": 0,
                "request_id": "",
                "cache_hit": False,
                "cache_scope": "session",
            },
            "error": {"code": code, "message": message, "retryable": retryable},
        }
        typer.echo(json.dumps(payload, ensure_ascii=False))
    else:
        typer.echo(f"error: {message}", err=True)
    raise typer.Exit(code=code)


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
