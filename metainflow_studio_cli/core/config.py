from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    provider_base_url: str
    provider_api_key: str
    summary_base_url: str
    summary_api_key: str
    provider_timeout_seconds: int
    provider_max_retries: int
    provider_model_doc_parse: str
    provider_model_web_search: str
    summary_model: str
    search_page_timeout_seconds: int
    web_search_backend: str
    search_provider_engine: str
    search_result_count: int
    searxng_base_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            provider_base_url=os.getenv("PROVIDER_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
            provider_api_key=os.getenv("PROVIDER_API_KEY", ""),
            summary_base_url=os.getenv(
                "SUMMARY_BASE_URL",
                os.getenv("PROVIDER_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
            ),
            summary_api_key=os.getenv(
                "SUMMARY_API_KEY",
                os.getenv("PROVIDER_API_KEY", ""),
            ),
            provider_timeout_seconds=int(os.getenv("PROVIDER_TIMEOUT_SECONDS", "60")),
            provider_max_retries=int(os.getenv("PROVIDER_MAX_RETRIES", "2")),
            provider_model_doc_parse=os.getenv("PROVIDER_MODEL_DOC_PARSE", "gpt-4.1-mini"),
            provider_model_web_search=os.getenv("PROVIDER_MODEL_WEB_SEARCH", "glm-4-air"),
            summary_model=os.getenv(
                "SUMMARY_MODEL",
                "glm-4-flash",
            ),
            search_page_timeout_seconds=int(
                os.getenv("SEARCH_PAGE_TIMEOUT_SECONDS", "30")
            ),
            web_search_backend=os.getenv("WEB_SEARCH_BACKEND", "auto"),
            search_provider_engine=os.getenv("SEARCH_PROVIDER_ENGINE", "search_pro"),
            search_result_count=int(os.getenv("SEARCH_RESULT_COUNT", "10")),
            searxng_base_url=os.getenv("SEARXNG_BASE_URL", "http://localhost:8080"),
        )
