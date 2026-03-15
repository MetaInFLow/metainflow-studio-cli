import pytest

from metainflow_studio_cli.core.errors import ExternalError
from metainflow_studio_cli.services.web_search.playwright_search_provider import search_web_with_playwright


class _FakeLocator:
    def __init__(self, count: int) -> None:
        self._count = count

    def count(self) -> int:
        return self._count


class _FakeResultNode:
    def __init__(self, title: str, url: str, snippet: str) -> None:
        self._title = title
        self._url = url
        self._snippet = snippet

    def locator(self, selector: str):
        if selector == "h3 a":
            return _FakeTextLocator(self._title, self._url)
        if selector in {".c-abstract, .content-right_8Zs40", '[data-sanssr-cmpt="card/www-summary"]'}:
            return _FakeTextLocator(self._snippet, None)
        return _FakeTextLocator("", None)


class _FakeElementHandleNode:
    def __init__(self, title: str, url: str, snippet: str, *, snippet_selector: str = '.c-abstract, .content-right_8Zs40') -> None:
        self._title = title
        self._url = url
        self._snippet = snippet
        self._snippet_selector = snippet_selector

    def query_selector(self, selector: str):
        if selector == "h3 a":
            return _FakeElementHandleText(self._title, self._url)
        if selector == self._snippet_selector:
            return _FakeElementHandleText(self._snippet, None)
        return None


class _FakeElementHandleText:
    def __init__(self, text: str, href: str | None) -> None:
        self._text = text
        self._href = href

    def inner_text(self) -> str:
        return self._text

    def get_attribute(self, name: str) -> str | None:
        if name == "href":
            return self._href
        return None


class _FakeTextLocator:
    def __init__(self, text: str, href: str | None) -> None:
        self._text = text
        self._href = href

    def inner_text(self) -> str:
        return self._text

    def get_attribute(self, name: str) -> str | None:
        if name == "href":
            return self._href
        return None

    def count(self) -> int:
        return 1 if self._text or self._href else 0


class _FakePage:
    def __init__(self, *, results: list[_FakeResultNode], captcha: bool = False, no_results: bool = False) -> None:
        self._results = results
        self._captcha = captcha
        self._no_results = no_results
        self.goto_url: str | None = None
        self.goto_timeout: int | None = None

    def goto(self, url: str, wait_until: str, timeout: int) -> None:
        self.goto_url = url
        self.goto_timeout = timeout

    def locator(self, selector: str):
        if selector == "#content_left .result, #content_left .c-container":
            return _FakeLocator(len(self._results))
        if selector == "#content_left":
            return _FakeLocator(1)
        if selector == "#captcha, .vcode-body":
            return _FakeLocator(1 if self._captcha else 0)
        if selector == ".no-result":
            return _FakeLocator(1 if self._no_results else 0)
        return _FakeLocator(0)

    def query_selector_all(self, selector: str) -> list[_FakeResultNode]:
        if selector == "#content_left .result, #content_left .c-container":
            return self._results
        return []


class _FakeBrowser:
    def __init__(self, page: _FakePage) -> None:
        self._page = page

    def new_page(self) -> _FakePage:
        return self._page

    def close(self) -> None:
        return None


class _FakeChromium:
    def __init__(self, page: _FakePage) -> None:
        self._page = page

    def launch(self, headless: bool) -> _FakeBrowser:
        return _FakeBrowser(self._page)


class _FakePlaywrightContext:
    def __init__(self, page: _FakePage) -> None:
        self.chromium = _FakeChromium(page)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FallbackPage(_FakePage):
    def __init__(self, outcomes: list[dict]) -> None:
        super().__init__(results=[])
        self._outcomes = outcomes
        self._index = -1
        self.goto_history: list[str] = []

    def goto(self, url: str, wait_until: str, timeout: int) -> None:
        self.goto_history.append(url)
        self._index += 1
        current = self._outcomes[self._index]
        self._captcha = current.get("captcha", False)
        self._no_results = current.get("no_results", False)
        self._results = current.get("results", [])
        self.goto_url = url
        self.goto_timeout = timeout


def test_search_web_with_playwright_fetches_and_normalizes_results(monkeypatch) -> None:
    page = _FakePage(
        results=[
            _FakeResultNode("Result 1", "https://example.com/1", "Snippet 1"),
            _FakeResultNode("Result 2", "https://example.com/2", "Snippet 2"),
        ]
    )
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.playwright_search_provider.sync_playwright",
        lambda: _FakePlaywrightContext(page),
    )

    result = search_web_with_playwright("React 19 新特性", timeout_seconds=12)

    assert page.goto_url.startswith("https://www.baidu.com/s?")
    assert "wd=React+19+%E6%96%B0%E7%89%B9%E6%80%A7" in page.goto_url
    assert page.goto_timeout == 12000
    assert result["provider"] == "baidu-playwright"
    assert result["results"] == [
        {"title": "Result 1", "url": "https://example.com/1", "snippet": "Snippet 1"},
        {"title": "Result 2", "url": "https://example.com/2", "snippet": "Snippet 2"},
    ]


def test_search_web_with_playwright_returns_empty_results(monkeypatch) -> None:
    page = _FakePage(results=[], no_results=True)
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.playwright_search_provider.sync_playwright",
        lambda: _FakePlaywrightContext(page),
    )

    result = search_web_with_playwright("unlikely query", timeout_seconds=12)

    assert result["provider"] == "baidu-playwright"
    assert result["results"] == []


def test_search_web_with_playwright_detects_captcha(monkeypatch) -> None:
    page = _FakePage(results=[], captcha=True)
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.playwright_search_provider.sync_playwright",
        lambda: _FakePlaywrightContext(page),
    )

    with pytest.raises(ExternalError, match="baidu search requires captcha verification"):
        search_web_with_playwright("query", timeout_seconds=12)


def test_search_web_with_playwright_maps_browser_errors(monkeypatch) -> None:
    def fail_start_browser(*args, **kwargs):
        raise RuntimeError("browser failed")

    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.playwright_search_provider.start_browser",
        fail_start_browser,
    )

    with pytest.raises(ExternalError, match="failed to launch undetected Playwright search"):
        search_web_with_playwright("query", timeout_seconds=12)


def test_search_web_with_playwright_supports_element_handle_nodes(monkeypatch) -> None:
    page = _FakePage(results=[_FakeElementHandleNode("Result 1", "https://example.com/1", "Snippet 1")])
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.playwright_search_provider.sync_playwright",
        lambda: _FakePlaywrightContext(page),
    )

    result = search_web_with_playwright("React 19 新特性", timeout_seconds=12)

    assert result["results"] == [
        {"title": "Result 1", "url": "https://example.com/1", "snippet": "Snippet 1"}
    ]


def test_search_web_with_playwright_uses_baidu_summary_selector(monkeypatch) -> None:
    page = _FakePage(
        results=[
            _FakeElementHandleNode(
                "Result 1",
                "https://example.com/1",
                "Summary from baidu card",
                snippet_selector='[data-sanssr-cmpt="card/www-summary"]',
            )
        ]
    )
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.playwright_search_provider.sync_playwright",
        lambda: _FakePlaywrightContext(page),
    )

    result = search_web_with_playwright("React 19 新特性", timeout_seconds=12)

    assert result["results"][0]["snippet"] == "Summary from baidu card"


def test_search_web_with_playwright_returns_empty_results_for_no_result_page(monkeypatch) -> None:
    page = _FakePage(results=[], no_results=True)
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.playwright_search_provider.sync_playwright",
        lambda: _FakePlaywrightContext(page),
    )

    result = search_web_with_playwright("React 19 新特性", timeout_seconds=12)

    assert result["results"] == []


def test_search_web_with_playwright_falls_back_to_mobile_baidu(monkeypatch) -> None:
    page = _FallbackPage(
        outcomes=[
            {"captcha": True, "results": []},
            {"results": [_FakeElementHandleNode("Result 1", "https://example.com/1", "Snippet 1")]},
        ]
    )
    monkeypatch.setattr(
        "metainflow_studio_cli.services.web_search.playwright_search_provider.sync_playwright",
        lambda: _FakePlaywrightContext(page),
    )

    result = search_web_with_playwright("React 19 新特性", timeout_seconds=12)

    assert page.goto_history[0].startswith("https://www.baidu.com/s?")
    assert page.goto_history[1].startswith("https://m.baidu.com/s?")
    assert result["results"][0]["title"] == "Result 1"
