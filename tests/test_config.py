from metainflow_studio_cli.core.config import Settings


def test_provider_prefix_env_loading(monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("PROVIDER_API_KEY", "secret")
    monkeypatch.setenv("SUMMARY_BASE_URL", "https://summary.example.com/v1")
    monkeypatch.setenv("SUMMARY_API_KEY", "summary-secret")
    monkeypatch.setenv("SUMMARY_MODEL", "summary-model")
    monkeypatch.setenv("SEARCH_PAGE_TIMEOUT_SECONDS", "25")
    monkeypatch.setenv("WEB_SEARCH_BACKEND", "auto")
    monkeypatch.setenv("SEARCH_PROVIDER_ENGINE", "search_pro")
    monkeypatch.setenv("SEARCH_RESULT_COUNT", "8")
    monkeypatch.setenv("SEARXNG_BASE_URL", "http://searx.local:8080")

    settings = Settings.from_env()

    assert settings.provider_base_url == "https://example.com/v1"
    assert settings.provider_api_key == "secret"
    assert settings.summary_base_url == "https://summary.example.com/v1"
    assert settings.summary_api_key == "summary-secret"
    assert settings.provider_model_web_search == "glm-4-air"
    assert settings.summary_model == "summary-model"
    assert settings.search_page_timeout_seconds == 25
    assert settings.web_search_backend == "auto"
    assert settings.search_provider_engine == "search_pro"
    assert settings.search_result_count == 8
    assert settings.searxng_base_url == "http://searx.local:8080"

def test_summary_endpoint_and_key_fall_back_to_primary_provider(monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("PROVIDER_API_KEY", "secret")
    monkeypatch.delenv("SUMMARY_BASE_URL", raising=False)
    monkeypatch.delenv("SUMMARY_API_KEY", raising=False)

    settings = Settings.from_env()

    assert settings.summary_base_url == "https://example.com/v1"
    assert settings.summary_api_key == "secret"


def test_summary_model_defaults_to_glm_4_flash(monkeypatch) -> None:
    monkeypatch.delenv("SUMMARY_MODEL", raising=False)

    settings = Settings.from_env()

    assert settings.summary_model == "glm-4-flash"
