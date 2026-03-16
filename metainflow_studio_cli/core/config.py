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
    provider_model_web_fetch: str
    web_fetch_verify_ssl: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            provider_base_url=os.getenv("PROVIDER_BASE_URL", "https://api.openai.com/v1"),
            provider_api_key=os.getenv("PROVIDER_API_KEY", ""),
            provider_timeout_seconds=int(os.getenv("PROVIDER_TIMEOUT_SECONDS", "60")),
            provider_max_retries=int(os.getenv("PROVIDER_MAX_RETRIES", "2")),
            provider_model_doc_parse=os.getenv("PROVIDER_MODEL_DOC_PARSE", "gpt-4.1-mini"),
            provider_model_web_fetch=os.getenv("PROVIDER_MODEL_WEB_FETCH", "gpt-4.1-mini"),
            web_fetch_verify_ssl=os.getenv("METAINFLOW_WEB_FETCH_VERIFY_SSL", "1") not in {"0", "false", "FALSE"},
        )
