import json

import pytest

from metainflow_studio_cli.core.errors import ExternalError, ValidationError
from metainflow_studio_cli.services.enterprise_query import service as enterprise_service
from metainflow_studio_cli.services.enterprise_query.service import enterprise_balance, enterprise_query, enterprise_search


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200, text: str = "") -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = text or json.dumps(payload, ensure_ascii=False)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            req = httpx.Request("POST", "https://example.com")
            resp = httpx.Response(self.status_code, request=req, text=self.text)
            raise httpx.HTTPStatusError("boom", request=req, response=resp)

    def json(self) -> dict:
        return self._payload


def test_enterprise_query_decodes_nested_payload_and_cache(monkeypatch) -> None:
    enterprise_service._SESSION_CACHE.clear()
    calls: list[tuple[str, dict, dict]] = []

    def fake_post(url: str, *, params: dict, json: dict, timeout: int, verify: bool) -> _FakeResponse:
        calls.append((url, params, json))
        return _FakeResponse({"code": 200, "msg": "OK", "data": "{\"status\":\"200\",\"message\":\"操作成功\",\"sign\":\"abc\",\"data\":{\"name\":\"测试公司\"}}"})

    monkeypatch.setenv("METAINFLOW_ENTERPRISE_API_APP_ID", "appid")
    monkeypatch.setenv("METAINFLOW_ENTERPRISE_API_SECRET", "secret")
    monkeypatch.setattr("metainflow_studio_cli.services.enterprise_query.service.httpx.post", fake_post)

    first = enterprise_query(query_type="business", keyword="测试公司", output="json", session_id="sess-1")
    second = enterprise_query(query_type="business", keyword="测试公司", output="json", session_id="sess-1")

    assert len(calls) == 1
    assert first["data"]["response"]["data"]["name"] == "测试公司"
    assert first["meta"]["cache_hit"] is False
    assert second["meta"]["cache_hit"] is True
    assert second["meta"]["cache_scope"] == "session-id"


def test_enterprise_query_without_session_id_does_not_cache(monkeypatch) -> None:
    enterprise_service._SESSION_CACHE.clear()
    calls: list[tuple[str, dict, dict]] = []

    def fake_post(url: str, *, params: dict, json: dict, timeout: int, verify: bool) -> _FakeResponse:
        calls.append((url, params, json))
        return _FakeResponse({"code": 200, "msg": "OK", "data": "{\"status\":\"200\",\"message\":\"操作成功\",\"sign\":\"abc\",\"data\":{\"name\":\"测试公司\"}}"})

    monkeypatch.setenv("METAINFLOW_ENTERPRISE_API_APP_ID", "appid")
    monkeypatch.setenv("METAINFLOW_ENTERPRISE_API_SECRET", "secret")
    monkeypatch.setattr("metainflow_studio_cli.services.enterprise_query.service.httpx.post", fake_post)

    first = enterprise_query(query_type="business", keyword="测试公司", output="json")
    second = enterprise_query(query_type="business", keyword="测试公司", output="json")

    assert len(calls) == 2
    assert first["meta"]["cache_hit"] is False
    assert second["meta"]["cache_hit"] is False
    assert second["meta"]["cache_scope"] == "none"


def test_enterprise_search_normalizes_candidates(monkeypatch) -> None:
    enterprise_service._SESSION_CACHE.clear()

    def fake_post(url: str, *, params: dict, json: dict, timeout: int, verify: bool) -> _FakeResponse:
        return _FakeResponse(
            {
                "code": 200,
                "msg": "OK",
                "data": json_module.dumps(
                    {
                        "status": "200",
                        "message": "操作成功",
                        "sign": "req1",
                        "data": {
                            "total": 2,
                            "num": 2,
                            "items": [
                                {
                                    "name": "示例智能（深圳）科技有限公司",
                                    "oper_name": "张三",
                                    "credit_no": "91310000MA1234567X",
                                    "start_date": "2024-09-14",
                                    "reg_no": "440300123456789",
                                }
                            ],
                        },
                    },
                    ensure_ascii=False,
                ),
            }
        )

    monkeypatch.setenv("METAINFLOW_ENTERPRISE_API_APP_ID", "appid")
    monkeypatch.setenv("METAINFLOW_ENTERPRISE_API_SECRET", "secret")
    monkeypatch.setattr("metainflow_studio_cli.services.enterprise_query.service.httpx.post", fake_post)
    result = enterprise_search(keyword="示例智能", output="json", session_id="sess-1")
    assert result["data"]["candidates"][0]["credit_no"] == "91310000MA1234567X"


def test_enterprise_balance_parses_numeric_balance(monkeypatch) -> None:
    enterprise_service._SESSION_CACHE.clear()

    def fake_post(url: str, *, json: dict, timeout: int, verify: bool) -> _FakeResponse:
        return _FakeResponse({"code": 200, "msg": "OK", "data": 29.0})

    monkeypatch.setenv("METAINFLOW_ENTERPRISE_API_APP_ID", "appid")
    monkeypatch.setenv("METAINFLOW_ENTERPRISE_API_SECRET", "secret")
    monkeypatch.setattr("metainflow_studio_cli.services.enterprise_query.service.httpx.post", fake_post)
    result = enterprise_balance(output="json", session_id="sess-1")
    assert result["data"]["balance"]["balance"] == 29.0
    assert result["data"]["balance"]["state"] == "sufficient"


def test_enterprise_query_requires_credentials(monkeypatch) -> None:
    enterprise_service._SESSION_CACHE.clear()
    monkeypatch.delenv("METAINFLOW_ENTERPRISE_API_APP_ID", raising=False)
    monkeypatch.delenv("METAINFLOW_ENTERPRISE_API_SECRET", raising=False)
    with pytest.raises(ValidationError):
        enterprise_query(query_type="business", keyword="测试公司", output="json")


def test_enterprise_query_wraps_http_error(monkeypatch) -> None:
    enterprise_service._SESSION_CACHE.clear()

    def fake_post(url: str, *, params: dict, json: dict, timeout: int, verify: bool) -> _FakeResponse:
        return _FakeResponse({}, status_code=502, text="bad gateway")

    monkeypatch.setenv("METAINFLOW_ENTERPRISE_API_APP_ID", "appid")
    monkeypatch.setenv("METAINFLOW_ENTERPRISE_API_SECRET", "secret")
    monkeypatch.setattr("metainflow_studio_cli.services.enterprise_query.service.httpx.post", fake_post)
    with pytest.raises(ExternalError):
        enterprise_query(query_type="business", keyword="测试公司", output="json", session_id="sess-1", refresh=True)


json_module = json
