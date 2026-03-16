from types import SimpleNamespace

import pytest

from metainflow_studio_cli.core.errors import ExternalError, ProcessingError
from metainflow_studio_cli.services.web_fetch.fetcher import (
    _extract_links_from_result,
    _extract_markdown_from_result,
    fetch_page,
)


def test_extract_markdown_prefers_crawl4ai_markdown_string() -> None:
    result = SimpleNamespace(markdown="# Title\n\nBody")

    extracted = _extract_markdown_from_result(result, "<html></html>")

    assert extracted == "# Title\n\nBody"


def test_extract_markdown_falls_back_to_html_text() -> None:
    result = SimpleNamespace(markdown="")

    extracted = _extract_markdown_from_result(result, "<html><body><h1>Title</h1><p>Body</p></body></html>")

    assert "Title" in extracted
    assert "Body" in extracted


def test_extract_links_prefers_crawl4ai_links() -> None:
    result = SimpleNamespace(
        links={
            "internal": [{"href": "/docs", "text": "Docs"}],
            "external": [{"url": "https://example.com/blog", "title": "Blog"}],
        }
    )

    links = _extract_links_from_result(result, "", "https://example.com/start")

    assert links == [
        {"url": "https://example.com/docs", "text": "Docs"},
        {"url": "https://example.com/blog", "text": "Blog"},
    ]


def test_extract_links_falls_back_to_html_when_crawl4ai_links_missing() -> None:
    result = SimpleNamespace(links=None)

    links = _extract_links_from_result(
        result,
        '<html><body><a href="/docs">Docs</a><a href="https://example.com/blog">Blog</a></body></html>',
        "https://example.com/start",
    )

    assert links == [
        {"url": "https://example.com/docs", "text": "Docs"},
        {"url": "https://example.com/blog", "text": "Blog"},
    ]


def test_fetch_page_returns_crawl4ai_result(monkeypatch) -> None:
    def fake_asyncio_run(coro):
        coro.close()
        return {
            "title": "Example",
            "markdown": "# Example\n\nBody",
            "links": [{"url": "https://example.com/docs", "text": "Docs"}],
        }

    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.fetcher.asyncio.run", fake_asyncio_run)

    result = fetch_page("https://example.com")

    assert result["title"] == "Example"
    assert "Body" in result["markdown"]
    assert result["links"][0]["url"] == "https://example.com/docs"


def test_fetch_page_maps_runtime_error(monkeypatch) -> None:
    def fake_asyncio_run(coro):
        coro.close()
        raise RuntimeError("loop unavailable")

    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.fetcher.asyncio.run", fake_asyncio_run)

    with pytest.raises(ExternalError, match="loop unavailable"):
        fetch_page("https://example.com")


def test_fetch_page_raises_processing_error_for_empty_content(monkeypatch) -> None:
    def fake_asyncio_run(coro):
        coro.close()
        raise ProcessingError("web fetch response is empty")

    monkeypatch.setattr("metainflow_studio_cli.services.web_fetch.fetcher.asyncio.run", fake_asyncio_run)

    with pytest.raises(ProcessingError, match="web fetch response is empty"):
        fetch_page("https://example.com")
