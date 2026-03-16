from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    provider_base_url: str
    provider_api_key: str
    provider_timeout_seconds: int
    provider_max_retries: int
    provider_model_doc_parse: str
    summary_base_url: str = ""
    summary_api_key: str = ""
    provider_model_web_search: str = "glm-4-air"
    provider_model_web_fetch: str = "gpt-4.1-mini"
    summary_model: str = "glm-4-flash"
    search_page_timeout_seconds: int = 30
    web_search_backend: str = "auto"
    search_provider_engine: str = "search_pro"
    search_result_count: int = 10
    searxng_base_url: str = "http://localhost:8080"
    web_fetch_verify_ssl: bool = True
    enterprise_api_base_url: str = "https://test.jszypt.com:42211/admin/api/getTenantApi"
    enterprise_balance_url: str = "https://test.jszypt.com:42211/sys-tenant-hehe/query"
    enterprise_api_app_id: str = ""
    enterprise_api_secret: str = ""
    enterprise_api_verify_ssl: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            provider_base_url=os.getenv("PROVIDER_BASE_URL", "https://api.openai.com/v1"),
            provider_api_key=os.getenv("PROVIDER_API_KEY", ""),
            provider_timeout_seconds=int(os.getenv("PROVIDER_TIMEOUT_SECONDS", "60")),
            provider_max_retries=int(os.getenv("PROVIDER_MAX_RETRIES", "2")),
            provider_model_doc_parse=os.getenv("PROVIDER_MODEL_DOC_PARSE", "gpt-4.1-mini"),
            summary_base_url=os.getenv(
                "SUMMARY_BASE_URL",
                os.getenv("PROVIDER_BASE_URL", "https://api.openai.com/v1"),
            ),
            summary_api_key=os.getenv(
                "SUMMARY_API_KEY",
                os.getenv("PROVIDER_API_KEY", ""),
            ),
            provider_model_web_search=os.getenv("PROVIDER_MODEL_WEB_SEARCH", "glm-4-air"),
            provider_model_web_fetch=os.getenv("PROVIDER_MODEL_WEB_FETCH", "gpt-4.1-mini"),
            summary_model=os.getenv("SUMMARY_MODEL", "glm-4-flash"),
            search_page_timeout_seconds=int(os.getenv("SEARCH_PAGE_TIMEOUT_SECONDS", "30")),
            web_search_backend=os.getenv("WEB_SEARCH_BACKEND", "auto"),
            search_provider_engine=os.getenv("SEARCH_PROVIDER_ENGINE", "search_pro"),
            search_result_count=int(os.getenv("SEARCH_RESULT_COUNT", "10")),
            searxng_base_url=os.getenv("SEARXNG_BASE_URL", "http://localhost:8080"),
            web_fetch_verify_ssl=os.getenv("METAINFLOW_WEB_FETCH_VERIFY_SSL", "1") not in {"0", "false", "FALSE"},
            enterprise_api_base_url=os.getenv(
                "METAINFLOW_ENTERPRISE_API_BASE_URL",
                "https://test.jszypt.com:42211/admin/api/getTenantApi",
            ),
            enterprise_balance_url=os.getenv(
                "METAINFLOW_ENTERPRISE_BALANCE_URL",
                "https://test.jszypt.com:42211/sys-tenant-hehe/query",
            ),
            enterprise_api_app_id=os.getenv("METAINFLOW_ENTERPRISE_API_APP_ID", ""),
            enterprise_api_secret=os.getenv("METAINFLOW_ENTERPRISE_API_SECRET", ""),
            enterprise_api_verify_ssl=os.getenv("METAINFLOW_ENTERPRISE_API_VERIFY_SSL", "1")
            not in {"0", "false", "FALSE"},
        )
