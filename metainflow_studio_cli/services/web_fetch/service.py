from __future__ import annotations

import time

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError, ProcessingError, ValidationError
from metainflow_studio_cli.services.web_fetch.fetcher import fetch_page
from metainflow_studio_cli.services.web_fetch.summary_provider import summarize_page


def web_crawl(url: str, instruction: str = "", output: str = "text") -> dict:
    if output not in {"text", "json"}:
        raise ValidationError("--output must be one of: text, json")

    started = time.perf_counter()
    normalized_url = url.strip()
    if not normalized_url:
        raise ValidationError("--url must not be empty")

    normalized_instruction = instruction.strip()
    settings = Settings.from_env()
    fetch_result = fetch_page(
        normalized_url,
        timeout_seconds=settings.provider_timeout_seconds,
        verify_ssl=settings.web_fetch_verify_ssl,
    )

    summary_result: dict[str, str] | None = None
    if normalized_instruction:
        try:
            summary_result = summarize_page(
                url=normalized_url,
                title=fetch_result["title"],
                instruction=normalized_instruction,
                markdown=fetch_result["markdown"],
                settings=settings,
            )
        except ExternalError as exc:
            if output != "json":
                raise
            return {
                "success": False,
                "data": {
                    "markdown": fetch_result["markdown"],
                    "extracted": "",
                    "url": normalized_url,
                    "title": fetch_result["title"],
                    "instruction": normalized_instruction,
                    "links": fetch_result["links"],
                },
                "meta": {
                    "fetch_provider": "crawl4ai",
                    "summary_provider": "llm",
                    "model": settings.provider_model_web_fetch,
                    "latency_ms": int((time.perf_counter() - started) * 1000),
                    "request_id": "",
                },
                "error": {"code": 3, "message": str(exc), "retryable": True},
            }
        except ProcessingError as exc:
            if output != "json":
                raise
            return {
                "success": False,
                "data": {
                    "markdown": fetch_result["markdown"],
                    "extracted": "",
                    "url": normalized_url,
                    "title": fetch_result["title"],
                    "instruction": normalized_instruction,
                    "links": fetch_result["links"],
                },
                "meta": {
                    "fetch_provider": "crawl4ai",
                    "summary_provider": "llm",
                    "model": settings.provider_model_web_fetch,
                    "latency_ms": int((time.perf_counter() - started) * 1000),
                    "request_id": "",
                },
                "error": {"code": 1, "message": str(exc), "retryable": False},
            }

    extracted = summary_result["summary"] if summary_result else ""

    return {
        "success": True,
        "data": {
            "markdown": fetch_result["markdown"],
            "extracted": extracted,
            "url": normalized_url,
            "title": fetch_result["title"],
            "instruction": normalized_instruction,
            "links": fetch_result["links"],
        },
        "meta": {
            "fetch_provider": "crawl4ai",
            "summary_provider": summary_result["provider"] if summary_result else "none",
            "model": summary_result["model"] if summary_result else "",
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "request_id": summary_result["request_id"] if summary_result else "",
        },
        "error": None,
    }
