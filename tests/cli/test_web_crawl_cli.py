import json

from typer.testing import CliRunner

from metainflow_studio_cli.core.errors import ExternalError
from metainflow_studio_cli.main import app


runner = CliRunner()


def test_web_crawl_json_output(monkeypatch) -> None:
    def fake_web_crawl(url: str, instruction: str, output: str) -> dict:
        assert url == "https://example.com/page.html"
        assert instruction == "提取主要观点"
        assert output == "json"
        return {
            "success": True,
            "data": {
                "markdown": "# Example\n\nBody",
                "extracted": "summary text",
                "url": url,
                "title": "Example",
                "instruction": instruction,
                "links": [{"url": "https://example.com/docs", "text": "Docs"}],
            },
            "meta": {
                "fetch_provider": "crawl4ai",
                "summary_provider": "llm",
                "model": "fetch-model",
                "latency_ms": 10,
                "request_id": "resp_123",
            },
            "error": None,
        }

    monkeypatch.setattr("metainflow_studio_cli.main.web_crawl", fake_web_crawl)

    result = runner.invoke(
        app,
        ["web-crawl", "--url", "https://example.com/page.html", "--instruction", "提取主要观点", "--output", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["data"]["title"] == "Example"
    assert payload["meta"]["fetch_provider"] == "crawl4ai"


def test_web_crawl_text_output_prefers_extracted_text(monkeypatch) -> None:
    def fake_web_crawl(url: str, instruction: str, output: str) -> dict:
        return {
            "success": True,
            "data": {
                "markdown": "# Example\n\nBody",
                "extracted": "summary text",
                "url": url,
                "title": "Example",
                "instruction": instruction,
                "links": [],
            },
            "meta": {
                "fetch_provider": "crawl4ai",
                "summary_provider": "llm",
                "model": "fetch-model",
                "latency_ms": 0,
                "request_id": "resp_123",
            },
            "error": None,
        }

    monkeypatch.setattr("metainflow_studio_cli.main.web_crawl", fake_web_crawl)

    result = runner.invoke(app, ["web-crawl", "--url", "https://example.com/page.html", "--instruction", "提取主要观点"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "summary text"


def test_web_crawl_text_output_falls_back_to_markdown(monkeypatch) -> None:
    def fake_web_crawl(url: str, instruction: str, output: str) -> dict:
        return {
            "success": True,
            "data": {
                "markdown": "# Example\n\nBody",
                "extracted": "",
                "url": url,
                "title": "Example",
                "instruction": instruction,
                "links": [],
            },
            "meta": {
                "fetch_provider": "crawl4ai",
                "summary_provider": "none",
                "model": "",
                "latency_ms": 0,
                "request_id": "",
            },
            "error": None,
        }

    monkeypatch.setattr("metainflow_studio_cli.main.web_crawl", fake_web_crawl)

    result = runner.invoke(app, ["web-crawl", "--url", "https://example.com/page.html"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "# Example\n\nBody"


def test_web_crawl_help_works() -> None:
    result = runner.invoke(app, ["web-crawl", "--help"])

    assert result.exit_code == 0
    assert "--url" in result.stdout
    assert "--instruction" in result.stdout


def test_web_crawl_external_error_returns_retryable_payload(monkeypatch) -> None:
    def fake_web_crawl(url: str, instruction: str, output: str) -> dict:
        raise ExternalError("web fetch request failed")

    monkeypatch.setattr("metainflow_studio_cli.main.web_crawl", fake_web_crawl)

    result = runner.invoke(app, ["web-crawl", "--url", "https://example.com/page.html", "--output", "json"])

    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert payload["error"]["retryable"] is True
    assert payload["error"]["message"] == "web fetch request failed"
