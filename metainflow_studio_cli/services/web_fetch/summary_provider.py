from __future__ import annotations

import httpx

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError, ProcessingError

MAX_CONTENT_CHARS = 20_000


def summarize_page(url: str, title: str, instruction: str, markdown: str, settings: Settings) -> dict:
    trimmed = markdown.strip()
    if len(trimmed) > MAX_CONTENT_CHARS:
        trimmed = trimmed[:MAX_CONTENT_CHARS]

    prompt_lines = [
        f"URL: {url}",
        f"Title: {title or 'Unknown'}",
        "Content:",
        trimmed,
    ]
    if instruction:
        prompt_lines.append(f"Instruction: {instruction}")
    prompt_lines.append("Extract the most useful information from this page.")

    payload = {
        "model": settings.provider_model_web_fetch,
        "messages": [
            {"role": "system", "content": "You extract key information from web page content."},
            {"role": "user", "content": "\n".join(prompt_lines)},
        ],
    }

    try:
        response = httpx.post(
            f"{settings.provider_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.provider_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=settings.provider_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ExternalError("web fetch summary request failed") from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise ProcessingError("summary response is not valid JSON") from exc

    choices = body.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ProcessingError("summary response missing message content")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ProcessingError("summary response missing message content")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ProcessingError("summary response missing message content")

    return {
        "summary": content.strip(),
        "provider": "llm",
        "model": body.get("model", settings.provider_model_web_fetch),
        "request_id": body.get("id", ""),
    }
