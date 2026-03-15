import pytest

from metainflow_studio_cli.core.errors import ExternalError, ValidationError
from metainflow_studio_cli.services.web_search.service import search_summary


def test_search_summary_rejects_empty_query() -> None:
    with pytest.raises(ValidationError, match="--query must not be empty"):
        search_summary(query="   ", instruction="", output="json")


def test_search_summary_returns_standard_envelope(monkeypatch) -> None:
    def fake_search_web(query: str, settings) -> dict:
        assert query == "React 19 新特性"
        return {
            "provider": "zhipu-web-search",
            "results": [{"title": "Result 1", "url": "https://example.com/1", "snippet": "snippet 1"}],
        }

    def fake_summarize_search_results(query: str, instruction: str, results: list[dict[str, str]], settings) -> dict:
        assert instruction == "按功能分类整理"
        assert results[0]["url"] == "https://example.com/1"
        return {
            "summary": "summary text",
            "provider": "llm",
            "model": "search-model",
            "request_id": "resp_123",
        }

    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.service.search_web",
        fake_search_web,
    )
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.service.summarize_search_results",
        fake_summarize_search_results,
    )

    result = search_summary(query="React 19 新特性", instruction="按功能分类整理", output="json")

    assert result["success"] is True
    assert result["data"]["summary"] == "summary text"
    assert result["data"]["query"] == "React 19 新特性"
    assert result["data"]["instruction"] == "按功能分类整理"
    assert result["data"]["results"][0]["title"] == "Result 1"
    assert result["meta"]["search_provider"] == "zhipu-web-search"
    assert result["meta"]["summary_provider"] == "llm"
    assert result["meta"]["model"] == "search-model"
    assert result["meta"]["request_id"] == "resp_123"
    assert result["error"] is None


def test_search_summary_propagates_search_errors(monkeypatch) -> None:
    def fake_search_web(query: str, settings) -> dict:
        raise ExternalError("web search request failed")

    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.service.search_web",
        fake_search_web,
    )

    with pytest.raises(ExternalError, match="web search request failed"):
        search_summary(query="React 19 新特性", instruction="", output="json")


def test_search_summary_handles_empty_search_results_without_model_call(monkeypatch) -> None:
    def fake_search_web(query: str, settings) -> dict:
        return {"provider": "zhipu-web-search", "results": []}

    def fake_summarize_search_results(query: str, instruction: str, results: list[dict[str, str]], settings) -> dict:
        raise AssertionError("summary provider should not be called for empty results")

    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.service.search_web",
        fake_search_web,
    )
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.service.summarize_search_results",
        fake_summarize_search_results,
    )

    result = search_summary(query="unlikely query", instruction="", output="json")

    assert result["success"] is True
    assert result["data"]["results"] == []
    assert result["data"]["summary"] == "No relevant search results found."


def test_search_summary_does_not_call_summary_provider_for_empty_results(monkeypatch) -> None:
    def fake_search_web(query: str, settings) -> dict:
        return {"provider": "zhipu-web-search", "results": []}

    def fail_summary_provider(query: str, instruction: str, results: list[dict[str, str]], settings) -> dict:
        raise AssertionError("summary provider should not be called for empty results")

    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.service.search_web",
        fake_search_web,
    )
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.service.summarize_search_results",
        fail_summary_provider,
    )

    result = search_summary(query="unlikely query", instruction="", output="json")

    assert result["data"]["summary"] == "No relevant search results found."


def test_search_summary_preserves_results_when_summary_fails_in_json_mode(monkeypatch) -> None:
    def fake_search_web(query: str, settings) -> dict:
        return {
            "provider": "zhipu-web-search",
            "results": [{"title": "Result 1", "url": "https://example.com/1", "snippet": "snippet 1"}],
        }

    def fake_summarize_search_results(query: str, instruction: str, results: list[dict[str, str]], settings) -> dict:
        raise ExternalError("web search summary request failed")

    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.service.search_web",
        fake_search_web,
    )
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.service.summarize_search_results",
        fake_summarize_search_results,
    )

    result = search_summary(query="React 19 新特性", instruction="", output="json")

    assert result["success"] is False
    assert result["data"]["results"][0]["url"] == "https://example.com/1"
    assert result["error"]["message"] == "web search summary request failed"
    assert result["error"]["retryable"] is True


def test_search_summary_falls_back_to_playwright_when_provider_search_fails(monkeypatch) -> None:
    calls: list[str] = []

    def fake_search_web(query: str, settings) -> dict:
        calls.append("search")
        return {
            "provider": "baidu-playwright",
            "results": [{"title": "Result 1", "url": "https://example.com/1", "snippet": "snippet 1"}],
        }

    def fake_summarize_search_results(query: str, instruction: str, results: list[dict[str, str]], settings) -> dict:
        calls.append("summary")
        return {
            "summary": "summary text",
            "provider": "llm",
            "model": "search-model",
            "request_id": "resp_123",
        }

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.service.search_web", fake_search_web)
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.service.summarize_search_results",
        fake_summarize_search_results,
    )

    result = search_summary(query="React 19 新特性", instruction="", output="json")

    assert calls == ["search", "summary"]
    assert result["meta"]["search_provider"] == "baidu-playwright"
