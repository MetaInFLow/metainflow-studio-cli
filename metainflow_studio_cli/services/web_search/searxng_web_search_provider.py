from __future__ import annotations

import httpx

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError


def search_web_with_searxng(query: str, settings: Settings) -> dict:
    searxng_url = f"{settings.searxng_base_url.rstrip('/')}/search"
    
    try:
        response = httpx.get(
            searxng_url,
            params={
                "q": query,
                "format": "json",
            },
            headers={"Accept": "application/json"},
            timeout=settings.provider_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ExternalError("SearXNG search request failed") from exc

    body = response.json()
    results = body.get("results", [])
    
    normalized = []
    for item in results[:settings.search_result_count]:
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        snippet = str(item.get("content") or "").strip()
        if title and url:
            normalized.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "source": str(item.get("engine") or "").strip(),
                    "publish_date": str(item.get("publishedDate") or "").strip(),
                }
            )

    return {
        "provider": "searxng-web-search",
        "request_id": "",
        "results": normalized,
    }
