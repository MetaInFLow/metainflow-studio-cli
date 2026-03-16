from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from metainflow_studio_cli.core.errors import ExternalError, ProcessingError

logger = logging.getLogger(__name__)

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
except ImportError:  # pragma: no cover - handled at runtime if dependency is missing
    AsyncWebCrawler = None
    BrowserConfig = None
    CacheMode = None
    CrawlerRunConfig = None


def extract_links(html: str, base_url: str) -> list[dict[str, str]]:
    """Extract links from HTML, making them absolute."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text(strip=True)
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        full_url = urljoin(base_url, href)
        if full_url not in seen_urls:
            seen_urls.add(full_url)
            links.append({"url": full_url, "text": text or full_url})

    return links


def format_links(links: list[dict[str, str]]) -> str:
    """Format links as a markdown list."""
    rendered = []
    for item in links:
        url = item.get("url", "").strip()
        text = item.get("text", "").strip() or url
        rendered.append(f"- [{text}]({url})")
    return "\n".join(rendered)


def _build_browser_config(verify_ssl: bool) -> Any:
    if BrowserConfig is None:
        return None
    try:
        return BrowserConfig(
            headless=True,
            user_agent="metainflow-studio-cli/0.1.0",
            ignore_https_errors=not verify_ssl,
        )
    except TypeError:
        return BrowserConfig(headless=True, user_agent="metainflow-studio-cli/0.1.0")


def _build_run_config(timeout_seconds: int) -> Any:
    if CrawlerRunConfig is None:
        return None
    timeout_ms = int(timeout_seconds * 1000)
    try:
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS if CacheMode else None,
            page_timeout=timeout_ms,
            wait_until="networkidle",
        )
    except TypeError:
        return CrawlerRunConfig(page_timeout=timeout_ms)


def _extract_title_from_html(html: str) -> str:
    if not html.strip():
        return ""
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""


def _extract_markdown_from_result(result: Any, html: str) -> str:
    markdown = ""
    if result is not None and getattr(result, "markdown", None):
        md = result.markdown
        if isinstance(md, str):
            markdown = md
        else:
            markdown = getattr(md, "raw_markdown", "") or getattr(md, "markdown", "") or ""

    if not markdown and html.strip():
        logger.warning("Primary extraction returned empty, falling back to basic text extraction")
        soup = BeautifulSoup(html, "html.parser")
        markdown = soup.get_text(separator="\n", strip=True)

    return markdown.strip()


def _extract_links_from_result(result: Any, html: str, base_url: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    raw_links = getattr(result, "links", None) if result is not None else None
    link_items: list[Any] = []
    if isinstance(raw_links, dict):
        for group in raw_links.values():
            if isinstance(group, list):
                link_items.extend(group)
    elif isinstance(raw_links, list):
        link_items.extend(raw_links)

    for item in link_items:
        if isinstance(item, dict):
            href = item.get("href") or item.get("url")
            text = item.get("text") or item.get("title") or href
        elif isinstance(item, str):
            href = item
            text = item
        else:
            continue
        if not href:
            continue
        full_url = urljoin(base_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        links.append({"url": full_url, "text": (text or full_url).strip()})

    if not links and html.strip():
        links = extract_links(html, base_url)

    return links


async def _crawl_with_crawl4ai(url: str, timeout_seconds: int, verify_ssl: bool) -> dict[str, Any]:
    if AsyncWebCrawler is None:
        raise ExternalError("crawl4ai is required for web fetch but is not installed")

    browser_config = _build_browser_config(verify_ssl)
    run_config = _build_run_config(timeout_seconds)

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
    except Exception as exc:
        raise ExternalError(f"web fetch request failed: {exc}") from exc

    if result is None or not getattr(result, "success", True):
        error_message = getattr(result, "error_message", "") or "web fetch request failed"
        raise ExternalError(error_message)

    html = getattr(result, "html", "") or ""

    title = ""
    metadata = getattr(result, "metadata", None)
    if isinstance(metadata, dict):
        title = metadata.get("title", "") or ""
    if not title:
        title = _extract_title_from_html(html)

    extracted_text = _extract_markdown_from_result(result, html)
    if not extracted_text:
        raise ProcessingError("web fetch response is empty")

    links = _extract_links_from_result(result, html, url)

    markdown_parts: list[str] = []
    if title:
        markdown_parts.append(f"# {title}")
    markdown_parts.append(extracted_text)
    if links:
        markdown_parts.append("## Links")
        markdown_parts.append(format_links(links))

    return {
        "title": title,
        "markdown": "\n\n".join(markdown_parts).strip(),
        "links": links,
    }


def fetch_page(url: str, timeout_seconds: int = 30, verify_ssl: bool = True) -> dict:
    """
    Fetch a page using Crawl4AI, executing JavaScript when needed.
    """
    try:
        return asyncio.run(_crawl_with_crawl4ai(url, timeout_seconds, verify_ssl))
    except RuntimeError as exc:
        raise ExternalError(f"web fetch request failed: {exc}") from exc
