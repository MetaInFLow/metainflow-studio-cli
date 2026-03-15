import pytest

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError
from metainflow_studio_cli.services.web_search.search_provider import search_web


def _settings(backend: str = "auto") -> Settings:
    return Settings(
        provider_base_url="https://open.bigmodel.cn/api/paas/v4",
        provider_api_key="secret",
        summary_base_url="https://summary.example.com/v1",
        summary_api_key="summary-secret",
        provider_timeout_seconds=30,
        provider_max_retries=2,
        provider_model_doc_parse="doc-model",
        provider_model_web_search="search-model",
        summary_model="summary-model",
        search_page_timeout_seconds=25,
        web_search_backend=backend,
        search_provider_engine="search_pro",
        search_result_count=8,
        searxng_base_url="http://localhost:8080",
    )


def test_search_web_prefers_provider_backend_in_auto_mode(monkeypatch) -> None:
    calls: list[str] = []

    def fake_provider(query: str, settings: Settings) -> dict:
        calls.append("provider")
        return {"provider": "zhipu-web-search", "request_id": "req_123", "results": [{"title": "R1", "url": "https://example.com/1", "snippet": "S1"}]}

    def fake_searxng(query: str, settings: Settings) -> dict:
        calls.append("searxng")
        return {"provider": "searxng-web-search", "results": [{"title": "R3", "url": "https://example.com/3", "snippet": "S3"}]}

    def fake_playwright(query: str, timeout_seconds: int = 30) -> dict:
        calls.append("playwright")
        return {"provider": "baidu-playwright", "results": [{"title": "R2", "url": "https://example.com/2", "snippet": "S2"}]}

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_provider", fake_provider)
    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_searxng", fake_searxng)
    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_playwright", fake_playwright)

    result = search_web("query", _settings())

    assert calls == ["provider"]
    assert result["provider"] == "zhipu-web-search"


def test_search_web_falls_back_to_searxng_when_provider_fails(monkeypatch) -> None:
    calls: list[str] = []

    def fake_provider(query: str, settings: Settings) -> dict:
        calls.append("provider")
        raise ExternalError("provider web search request failed")

    def fake_searxng(query: str, settings: Settings) -> dict:
        calls.append("searxng")
        return {"provider": "searxng-web-search", "results": [{"title": "R3", "url": "https://example.com/3", "snippet": "S3"}]}

    def fake_playwright(query: str, timeout_seconds: int = 30) -> dict:
        calls.append("playwright")
        return {"provider": "baidu-playwright", "results": []}

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_provider", fake_provider)
    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_searxng", fake_searxng)
    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_playwright", fake_playwright)

    result = search_web("query", _settings())

    assert calls == ["provider", "searxng"]
    assert result["provider"] == "searxng-web-search"


def test_search_web_falls_back_to_playwright_when_searxng_fails(monkeypatch) -> None:
    calls: list[str] = []

    def fake_provider(query: str, settings: Settings) -> dict:
        calls.append("provider")
        raise ExternalError("provider web search request failed")

    def fake_searxng(query: str, settings: Settings) -> dict:
        calls.append("searxng")
        raise ExternalError("searxng web search request failed")

    def fake_playwright(query: str, timeout_seconds: int = 30) -> dict:
        calls.append("playwright")
        return {"provider": "baidu-playwright", "results": [{"title": "R2", "url": "https://example.com/2", "snippet": "S2"}]}

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_provider", fake_provider)
    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_searxng", fake_searxng)
    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_playwright", fake_playwright)

    result = search_web("query", _settings())

    assert calls == ["provider", "searxng", "playwright"]
    assert result["provider"] == "baidu-playwright"


def test_search_web_falls_back_when_returning_empty_list(monkeypatch) -> None:
    calls: list[str] = []

    def fake_provider(query: str, settings: Settings) -> dict:
        calls.append("provider")
        # Returns empty list, which should trigger fallback!
        return {"provider": "zhipu-web-search", "request_id": "req_123", "results": []}

    def fake_searxng(query: str, settings: Settings) -> dict:
        calls.append("searxng")
        return {"provider": "searxng-web-search", "results": [{"title": "R3", "url": "https://example.com/3", "snippet": "S3"}]}

    def fake_playwright(query: str, timeout_seconds: int = 30) -> dict:
        calls.append("playwright")
        return {"provider": "baidu-playwright", "results": [{"title": "R2", "url": "https://example.com/2", "snippet": "S2"}]}

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_provider", fake_provider)
    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_searxng", fake_searxng)
    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_playwright", fake_playwright)

    result = search_web("query", _settings())

    # Should have fallen back because provider returned empty list
    assert calls == ["provider", "searxng"]
    assert result["provider"] == "searxng-web-search"


def test_search_web_uses_provider_only_when_backend_forced(monkeypatch) -> None:
    calls: list[str] = []

    def fake_provider(query: str, settings: Settings) -> dict:
        calls.append("provider")
        return {"provider": "zhipu-web-search", "request_id": "req_123", "results": [{"title": "R1", "url": "https://example.com/1", "snippet": "S1"}]}

    def fake_searxng(query: str, settings: Settings) -> dict:
        calls.append("searxng")
        return {"provider": "searxng-web-search", "results": []}

    def fake_playwright(query: str, timeout_seconds: int = 30) -> dict:
        calls.append("playwright")
        return {"provider": "baidu-playwright", "results": [{"title": "R2", "url": "https://example.com/2", "snippet": "S2"}]}

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_provider", fake_provider)
    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_searxng", fake_searxng)
    monkeypatch.setattr("metainflow_studio_cli.services.web_search.search_provider.search_web_with_playwright", fake_playwright)

    result = search_web("query", _settings(backend="searxng-web-search"))

    assert calls == ["searxng"]
    assert result["provider"] == "searxng-web-search"
