import httpx
import pytest

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError, ProcessingError
from metainflow_studio_cli.services.web_search.zhipu_web_search_provider import search_web_with_provider


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def _settings() -> Settings:
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
        web_search_backend="auto",
        search_provider_engine="search_pro",
        search_result_count=8,
        searxng_base_url="http://localhost:8080",
    )


def test_search_web_with_provider_builds_request_and_normalizes_response(monkeypatch) -> None:
    seen: dict = {}

    def fake_post(url: str, *, headers: dict, json: dict, timeout: int) -> _FakeResponse:
        seen["url"] = url
        seen["headers"] = headers
        seen["json"] = json
        seen["timeout"] = timeout
        return _FakeResponse(
            {
                "request_id": "req_123",
                "search_result": [
                    {
                        "title": "Result 1",
                        "link": "https://example.com/1",
                        "content": "Snippet 1",
                        "media": "Example",
                        "publish_date": "2025-01-01",
                    }
                ],
            }
        )

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.zhipu_web_search_provider.httpx.post", fake_post)

    result = search_web_with_provider("React 19 新特性", _settings())

    assert seen["url"] == "https://open.bigmodel.cn/api/paas/v4/tools"
    assert seen["headers"]["Authorization"] == "Bearer secret"
    assert seen["json"]["tool"] == "web-search-pro"
    assert seen["json"]["messages"][0]["content"] == "React 19 新特性"
    assert seen["json"]["search_engine"] == "search_pro"
    assert seen["json"]["count"] == 8
    assert result["provider"] == "zhipu-web-search"
    assert result["request_id"] == "req_123"
    assert result["results"] == [
        {
            "title": "Result 1",
            "url": "https://example.com/1",
            "snippet": "Snippet 1",
            "source": "Example",
            "publish_date": "2025-01-01",
        }
    ]


def test_search_web_with_provider_supports_tool_call_response_shape(monkeypatch) -> None:
    def fake_post(url: str, *, headers: dict, json: dict, timeout: int) -> _FakeResponse:
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "tool",
                            "tool_calls": [
                                {
                                    "type": "search_result",
                                    "search_result": [
                                        {
                                            "title": "Result 1",
                                            "link": "https://example.com/1",
                                            "content": "Snippet 1",
                                            "media": "Example",
                                            "publish_date": "2025-01-01",
                                        }
                                    ],
                                }
                            ],
                        }
                    }
                ],
                "request_id": "req_nested",
            }
        )

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.zhipu_web_search_provider.httpx.post", fake_post)

    result = search_web_with_provider("React 19 新特性", _settings())

    assert result["provider"] == "zhipu-web-search"
    assert result["request_id"] == "req_nested"
    assert result["results"][0]["title"] == "Result 1"


def test_search_web_with_provider_raises_processing_error_for_bad_shape(monkeypatch) -> None:
    def fake_post(url: str, *, headers: dict, json: dict, timeout: int) -> _FakeResponse:
        return _FakeResponse({"request_id": "req_123", "search_result": {}})

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.zhipu_web_search_provider.httpx.post", fake_post)

    with pytest.raises(ProcessingError, match="provider web search returned invalid search_result"):
        search_web_with_provider("query", _settings())


def test_search_web_with_provider_maps_http_errors(monkeypatch) -> None:
    def fake_post(url: str, *, headers: dict, json: dict, timeout: int):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.zhipu_web_search_provider.httpx.post", fake_post)

    with pytest.raises(ExternalError, match="provider web search request failed"):
        search_web_with_provider("query", _settings())
