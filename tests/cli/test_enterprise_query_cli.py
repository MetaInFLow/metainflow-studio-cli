import json

from typer.testing import CliRunner

from metainflow_studio_cli.core.errors import ExternalError
from metainflow_studio_cli.main import app


runner = CliRunner()


def test_enterprise_query_json_output(monkeypatch) -> None:
    def fake_enterprise_query(query_type: str, keyword: str, output: str, session_id: str, skip: int, role_code: str, role_history: str, refresh: bool) -> dict:
        assert query_type == "business"
        assert keyword == "测试公司"
        assert output == "json"
        assert session_id == "sess-1"
        assert refresh is True
        return {
            "success": True,
            "data": {
                "markdown": "# 工商信息",
                "query_type": "business",
                "display_name": "工商信息",
                "keyword": keyword,
                "api_id": "1.41",
                "billing": "0.1元/次",
                "input_params": {"keyword": keyword},
                "response": {"status": "200", "data": {"name": keyword}},
                "is_empty": False,
            },
            "meta": {
                "provider": "yuanjian",
                "endpoint": "https://example.com",
                "latency_ms": 10,
                "request_id": "req",
                "cache_hit": False,
                "cache_scope": "session-id",
            },
            "error": None,
        }

    monkeypatch.setattr("metainflow_studio_cli.main.enterprise_query", fake_enterprise_query)
    result = runner.invoke(
        app,
        ["enterprise-query", "--type", "business", "--keyword", "测试公司", "--session-id", "sess-1", "--refresh", "--output", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["api_id"] == "1.41"


def test_enterprise_search_text_output(monkeypatch) -> None:
    def fake_enterprise_search(keyword: str, output: str, session_id: str, refresh: bool) -> dict:
        return {
            "success": True,
            "data": {
                "markdown": "# 企业搜索",
                "keyword": keyword,
                "api_id": "1.31",
                "response": {},
                "candidates": [],
                "is_empty": True,
            },
            "meta": {
                "provider": "yuanjian",
                "endpoint": "https://example.com",
                "latency_ms": 0,
                "request_id": "",
                "cache_hit": True,
                "cache_scope": "session-id",
            },
            "error": None,
        }

    monkeypatch.setattr("metainflow_studio_cli.main.enterprise_search", fake_enterprise_search)
    result = runner.invoke(app, ["enterprise-search", "--keyword", "示例智能"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "# 企业搜索"


def test_enterprise_balance_external_error_returns_retryable_payload(monkeypatch) -> None:
    def fake_enterprise_balance(output: str, session_id: str, refresh: bool) -> dict:
        raise ExternalError("enterprise balance request failed")

    monkeypatch.setattr("metainflow_studio_cli.main.enterprise_balance", fake_enterprise_balance)
    result = runner.invoke(app, ["enterprise-balance", "--output", "json"])
    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["error"]["retryable"] is True
