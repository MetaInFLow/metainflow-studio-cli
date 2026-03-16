from metainflow_studio_cli.core.config import Settings


def test_provider_prefix_env_loading(monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("PROVIDER_API_KEY", "secret")
    monkeypatch.setenv("PROVIDER_MODEL_WEB_FETCH", "fetch-model")
    monkeypatch.setenv("METAINFLOW_WEB_FETCH_VERIFY_SSL", "0")

    settings = Settings.from_env()

    assert settings.provider_base_url == "https://example.com/v1"
    assert settings.provider_api_key == "secret"
    assert settings.provider_model_web_fetch == "fetch-model"
    assert settings.web_fetch_verify_ssl is False
