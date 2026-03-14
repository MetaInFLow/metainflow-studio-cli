from metainflow_studio_cli.core.config import Settings


def test_provider_prefix_env_loading(monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("PROVIDER_API_KEY", "secret")

    settings = Settings.from_env()

    assert settings.provider_base_url == "https://example.com/v1"
    assert settings.provider_api_key == "secret"
