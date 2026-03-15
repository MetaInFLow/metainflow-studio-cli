from __future__ import annotations

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError
from metainflow_studio_cli.services.web_search.playwright_search_provider import search_web_with_playwright
from metainflow_studio_cli.services.web_search.zhipu_web_search_provider import search_web_with_provider
from metainflow_studio_cli.services.web_search.searxng_web_search_provider import search_web_with_searxng


def search_web(query: str, settings: Settings) -> dict:
    backend = settings.web_search_backend
    if backend == "searxng-web-search":
        return search_web_with_searxng(query, settings)
    if backend == "zhipu-web-search":
        return search_web_with_provider(query, settings)
    if backend == "baidu-playwright":
        return search_web_with_playwright(query, timeout_seconds=settings.search_page_timeout_seconds)

    last_error: ExternalError | None = None
    for runner in (
        lambda: search_web_with_provider(query, settings),
        lambda: search_web_with_searxng(query, settings),
        lambda: search_web_with_playwright(query, timeout_seconds=settings.search_page_timeout_seconds),
    ):
        try:
            result = runner()
            if not result.get("results"):
                raise ExternalError("Provider returned empty, forcing fallback")
            return result
        except ExternalError as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    return {"provider": "zhipu-web-search", "request_id": "", "results": []}
