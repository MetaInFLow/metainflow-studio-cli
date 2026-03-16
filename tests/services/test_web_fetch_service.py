import pytest

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError, ProcessingError, ValidationError
from metainflow_studio_cli.services.web_fetch.service import web_crawl


def _settings() -> Settings:
    return Settings(
        provider_base_url="https://api.example.com/v1",
        provider_api_key="secret",
        provider_timeout_seconds=30,
        provider_max_retries=2,
        provider_model_doc_parse="doc-model",
        provider_model_web_fetch="fetch-model",
        web_fetch_verify_ssl=True,
    )


def test_web_crawl_rejects_empty_url() -> None:
    with pytest.raises(ValidationError, match="--url must not be empty"):
        web_crawl(url="   ", instruction="", output="json")


def test_web_crawl_returns_standard_envelope(monkeypatch) -> None:
    def fake_fetch_page(url: str, timeout_seconds: int, verify_ssl: bool) -> dict:
        assert url == "https://example.com"
        assert timeout_seconds == 30
        assert verify_ssl is True
        return {
            "title": "Example",
            "markdown": "# Example\n\nBody",
            "links": [{"url": "https://example.com/docs", "text": "Docs"}],
        }

    def fake_summarize_page(url: str, title: str, instruction: str, markdown: str, settings: Settings) -> dict:
        assert title == "Example"
        assert instruction == "提取重点"
        assert "Body" in markdown
        assert settings.provider_model_web_fetch == "fetch-model"
        return {
            "summary": "summary text",
            "provider": "llm",
            "model": "fetch-model",
            "request_id": "resp_123",
        }

    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.Settings.from_env", _settings)
    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.fetch_page", fake_fetch_page)
    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.summarize_page", fake_summarize_page)

    result = web_crawl(url="https://example.com", instruction="提取重点", output="json")

    assert result["success"] is True
    assert result["data"]["title"] == "Example"
    assert result["data"]["extracted"] == "summary text"
    assert result["meta"]["fetch_provider"] == "crawl4ai"
    assert result["meta"]["summary_provider"] == "llm"
    assert result["meta"]["model"] == "fetch-model"
    assert result["meta"]["request_id"] == "resp_123"


def test_web_crawl_skips_summary_when_instruction_empty(monkeypatch) -> None:
    def fake_fetch_page(url: str, timeout_seconds: int, verify_ssl: bool) -> dict:
        return {
            "title": "Example",
            "markdown": "# Example\n\nBody",
            "links": [],
        }

    def fail_summarize_page(**kwargs):
        raise AssertionError("summary should not be called when instruction is empty")

    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.Settings.from_env", _settings)
    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.fetch_page", fake_fetch_page)
    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.summarize_page", fail_summarize_page)

    result = web_crawl(url="https://example.com", instruction="   ", output="json")

    assert result["success"] is True
    assert result["data"]["extracted"] == ""
    assert result["meta"]["summary_provider"] == "none"


def test_web_crawl_preserves_fetch_result_when_summary_external_error_in_json_mode(monkeypatch) -> None:
    def fake_fetch_page(url: str, timeout_seconds: int, verify_ssl: bool) -> dict:
        return {
            "title": "Example",
            "markdown": "# Example\n\nBody",
            "links": [{"url": "https://example.com/docs", "text": "Docs"}],
        }

    def fake_summarize_page(url: str, title: str, instruction: str, markdown: str, settings: Settings) -> dict:
        raise ExternalError("web fetch summary request failed")

    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.Settings.from_env", _settings)
    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.fetch_page", fake_fetch_page)
    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.summarize_page", fake_summarize_page)

    result = web_crawl(url="https://example.com", instruction="提取重点", output="json")

    assert result["success"] is False
    assert result["data"]["markdown"] == "# Example\n\nBody"
    assert result["data"]["links"][0]["url"] == "https://example.com/docs"
    assert result["error"]["code"] == 3
    assert result["error"]["retryable"] is True


def test_web_crawl_preserves_fetch_result_when_summary_processing_error_in_json_mode(monkeypatch) -> None:
    def fake_fetch_page(url: str, timeout_seconds: int, verify_ssl: bool) -> dict:
        return {
            "title": "Example",
            "markdown": "# Example\n\nBody",
            "links": [],
        }

    def fake_summarize_page(url: str, title: str, instruction: str, markdown: str, settings: Settings) -> dict:
        raise ProcessingError("summary response is not valid JSON")

    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.Settings.from_env", _settings)
    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.fetch_page", fake_fetch_page)
    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.service.summarize_page", fake_summarize_page)

    result = web_crawl(url="https://example.com", instruction="提取重点", output="json")

    assert result["success"] is False
    assert result["data"]["title"] == "Example"
    assert result["error"]["code"] == 1
    assert result["error"]["retryable"] is False
