from __future__ import annotations

import httpx

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError, ProcessingError


def summarize_search_results(query: str, instruction: str, results: list[dict[str, str]], settings: Settings) -> dict:
    prompt_lines = [f"Query: {query}", "Search results:"]
    for index, item in enumerate(results, start=1):
        prompt_lines.append(f"{index}. {item['title']}")
        prompt_lines.append(f"URL: {item['url']}")
        prompt_lines.append(f"Snippet: {item['snippet']}")
    if instruction:
        prompt_lines.append(f"Instruction: {instruction}")
    prompt_lines.append("Summarize the most useful information from these search results.")

    payload = {
        "model": settings.summary_model,
        "messages": [
            {"role": "system", "content": "You summarize web search results into a concise helpful answer."},
            {"role": "user", "content": "\n".join(prompt_lines)},
        ],
    }

    try:
        response = httpx.post(
            f"{settings.summary_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.summary_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=settings.provider_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ExternalError("web search summary request failed") from exc

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
        "model": body.get("model", settings.summary_model),
        "request_id": body.get("id", ""),
    }
