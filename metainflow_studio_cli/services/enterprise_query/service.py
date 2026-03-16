from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError, ProcessingError, ValidationError


logger = logging.getLogger(__name__)
_SESSION_CACHE: dict[tuple[str, ...], dict[str, Any]] = {}


@dataclass(frozen=True, slots=True)
class QuerySpec:
    canonical_type: str
    display_name: str
    api_id: str
    keyword_param: str
    billing: str


QUERY_SPECS: dict[str, QuerySpec] = {
    "business": QuerySpec("business", "工商信息", "1.41", "keyword", "0.1元/次"),
    "qualification": QuerySpec("qualification", "资质证书", "22.1", "name", "0.1元/次"),
    "patent": QuerySpec("patent", "专利查询", "8.1", "name", "0.1元/次"),
    "annual-report": QuerySpec("annual-report", "年报信息", "3.1", "keyword", "0.1元/次"),
    "tax": QuerySpec("tax", "税号开票", "52.3", "keyword", "0.1元/次"),
}

QUERY_TYPE_ALIASES = {
    "business": "business",
    "工商": "business",
    "工商信息": "business",
    "qualification": "qualification",
    "资质": "qualification",
    "资质证书": "qualification",
    "patent": "patent",
    "专利": "patent",
    "专利查询": "patent",
    "annual-report": "annual-report",
    "annual_report": "annual-report",
    "annualreport": "annual-report",
    "年报": "annual-report",
    "年报信息": "annual-report",
    "tax": "tax",
    "taxpayer": "tax",
    "tax-info": "tax",
    "税号": "tax",
    "税号开票": "tax",
    "纳税人信息": "tax",
}


def enterprise_query(
    query_type: str,
    keyword: str,
    output: str = "text",
    skip: int = 0,
    role_code: str = "",
    role_history: str = "",
    session_id: str = "",
    refresh: bool = False,
) -> dict[str, Any]:
    if output not in {"text", "json"}:
        raise ValidationError("--output must be one of: text, json")
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        raise ValidationError("--keyword must not be empty")
    if skip < 0:
        raise ValidationError("--skip must be greater than or equal to 0")

    settings = _enterprise_settings()
    canonical_type = _normalize_query_type(query_type)
    spec = QUERY_SPECS[canonical_type]
    input_params: dict[str, Any] = {spec.keyword_param: normalized_keyword}
    if canonical_type in {"qualification", "patent"} and skip:
        input_params["skip"] = str(skip)
    if canonical_type == "patent":
        if role_code.strip():
            input_params["role_code"] = role_code.strip()
        if role_history.strip():
            input_params["role_history"] = role_history.strip()

    started = time.perf_counter()
    payload, cache_hit = _request_api(
        cache_namespace="detail",
        api_id=spec.api_id,
        input_params=input_params,
        settings=settings,
        session_id=session_id.strip(),
        refresh=refresh,
    )
    normalized = _normalize_query_payload(payload)
    latency_ms = 0 if cache_hit else int((time.perf_counter() - started) * 1000)
    return {
        "success": True,
        "data": {
            "markdown": _render_query_markdown(spec.display_name, spec.api_id, spec.billing, input_params, normalized),
            "query_type": spec.canonical_type,
            "display_name": spec.display_name,
            "keyword": normalized_keyword,
            "api_id": spec.api_id,
            "billing": spec.billing,
            "input_params": input_params,
            "response": normalized,
            "is_empty": normalized["is_empty"],
        },
        "meta": {
            "provider": "yuanjian",
            "endpoint": settings.enterprise_api_base_url,
            "latency_ms": latency_ms,
            "request_id": normalized["request_id"],
            "cache_hit": cache_hit,
            "cache_scope": "session-id" if session_id.strip() else "none",
        },
        "error": None,
    }


def enterprise_search(keyword: str, output: str = "text", session_id: str = "", refresh: bool = False) -> dict[str, Any]:
    if output not in {"text", "json"}:
        raise ValidationError("--output must be one of: text, json")
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        raise ValidationError("--keyword must not be empty")

    settings = _enterprise_settings()
    started = time.perf_counter()
    payload, cache_hit = _request_api(
        cache_namespace="search",
        api_id="1.31",
        input_params={"keyword": normalized_keyword},
        settings=settings,
        session_id=session_id.strip(),
        refresh=refresh,
    )
    normalized = _normalize_search_payload(payload)
    latency_ms = 0 if cache_hit else int((time.perf_counter() - started) * 1000)
    return {
        "success": True,
        "data": {
            "markdown": _render_search_markdown(normalized_keyword, normalized),
            "keyword": normalized_keyword,
            "api_id": "1.31",
            "response": normalized,
            "candidates": normalized["items"],
            "is_empty": normalized["is_empty"],
        },
        "meta": {
            "provider": "yuanjian",
            "endpoint": settings.enterprise_api_base_url,
            "latency_ms": latency_ms,
            "request_id": normalized["request_id"],
            "cache_hit": cache_hit,
            "cache_scope": "session-id" if session_id.strip() else "none",
        },
        "error": None,
    }


def enterprise_balance(output: str = "text", session_id: str = "", refresh: bool = False) -> dict[str, Any]:
    if output not in {"text", "json"}:
        raise ValidationError("--output must be one of: text, json")
    settings = _enterprise_settings()
    started = time.perf_counter()
    payload, cache_hit = _request_balance(settings=settings, session_id=session_id.strip(), refresh=refresh)
    normalized = _normalize_balance_payload(payload)
    latency_ms = 0 if cache_hit else int((time.perf_counter() - started) * 1000)
    return {
        "success": True,
        "data": {
            "markdown": _render_balance_markdown(normalized, payload),
            "balance": normalized,
            "response": payload,
        },
        "meta": {
            "provider": "yuanjian",
            "endpoint": settings.enterprise_balance_url,
            "latency_ms": latency_ms,
            "request_id": "",
            "cache_hit": cache_hit,
            "cache_scope": "session-id" if session_id.strip() else "none",
        },
        "error": None,
    }


def _enterprise_settings() -> Settings:
    settings = Settings.from_env()
    if not settings.enterprise_api_app_id.strip():
        raise ValidationError("METAINFLOW_ENTERPRISE_API_APP_ID is required")
    if not settings.enterprise_api_secret.strip():
        raise ValidationError("METAINFLOW_ENTERPRISE_API_SECRET is required")
    return settings


def _normalize_query_type(query_type: str) -> str:
    normalized = QUERY_TYPE_ALIASES.get(query_type.strip().lower())
    if normalized is None:
        allowed = ", ".join(sorted(QUERY_SPECS))
        raise ValidationError(f"--type must be one of: {allowed}")
    return normalized


def _request_api(
    cache_namespace: str,
    api_id: str,
    input_params: dict[str, Any],
    settings: Settings,
    session_id: str,
    refresh: bool,
) -> tuple[dict[str, Any], bool]:
    cache_key: tuple[str, ...] | None = None
    if session_id:
        cache_key = (
            "enterprise",
            session_id,
            cache_namespace,
            api_id,
            settings.enterprise_api_base_url,
            settings.enterprise_api_app_id,
            json.dumps(input_params, ensure_ascii=False, sort_keys=True),
        )
        if not refresh and cache_key in _SESSION_CACHE:
            logger.info("Enterprise session cache hit: session_id=%s api_id=%s params=%s", session_id, api_id, input_params)
            return _SESSION_CACHE[cache_key], True

    try:
        response = httpx.post(
            settings.enterprise_api_base_url,
            params={
                "appid": settings.enterprise_api_app_id,
                "secret": settings.enterprise_api_secret,
            },
            json={
                "apiId": api_id,
                "inputParams": json.dumps(input_params, ensure_ascii=False, separators=(",", ":")),
            },
            timeout=settings.provider_timeout_seconds,
            verify=settings.enterprise_api_verify_ssl,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ExternalError(f"enterprise query request failed: {exc.response.text.strip() or exc}") from exc
    except httpx.HTTPError as exc:
        raise ExternalError(f"enterprise query request failed: {exc}") from exc

    payload = _parse_json_response(response, "enterprise query")
    if cache_key is not None:
        _SESSION_CACHE[cache_key] = payload
    return payload, False


def _request_balance(settings: Settings, session_id: str, refresh: bool) -> tuple[dict[str, Any], bool]:
    cache_key: tuple[str, ...] | None = None
    if session_id:
        cache_key = (
            "enterprise",
            session_id,
            "balance",
            settings.enterprise_balance_url,
            settings.enterprise_api_app_id,
        )
        if not refresh and cache_key in _SESSION_CACHE:
            logger.info("Enterprise balance session cache hit: session_id=%s", session_id)
            return _SESSION_CACHE[cache_key], True

    try:
        response = httpx.post(
            settings.enterprise_balance_url,
            json={
                "appid": settings.enterprise_api_app_id,
                "secret": settings.enterprise_api_secret,
            },
            timeout=settings.provider_timeout_seconds,
            verify=settings.enterprise_api_verify_ssl,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ExternalError(f"enterprise balance request failed: {exc.response.text.strip() or exc}") from exc
    except httpx.HTTPError as exc:
        raise ExternalError(f"enterprise balance request failed: {exc}") from exc

    payload = _parse_json_response(response, "enterprise balance")
    if cache_key is not None:
        _SESSION_CACHE[cache_key] = payload
    return payload, False


def _parse_json_response(response: httpx.Response, label: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ProcessingError(f"{label} returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ProcessingError(f"{label} returned an unexpected payload")
    return payload


def _decode_nested_payload(payload: dict[str, Any]) -> dict[str, Any]:
    nested = payload.get("data")
    if isinstance(nested, str):
        try:
            decoded = json.loads(nested)
        except ValueError:
            return {"outer": payload, "inner": None}
        if isinstance(decoded, dict):
            return {"outer": payload, "inner": decoded}
    if isinstance(nested, dict):
        return {"outer": payload, "inner": nested}
    return {"outer": payload, "inner": None}


def _normalize_query_payload(payload: dict[str, Any]) -> dict[str, Any]:
    decoded = _decode_nested_payload(payload)
    outer = decoded["outer"]
    inner = decoded["inner"] if isinstance(decoded["inner"], dict) else {}
    status = str(inner.get("status", outer.get("code", "")))
    message = str(inner.get("message", outer.get("msg", "")))
    data = inner.get("data", {})
    is_empty = status == "201" or data in ({}, [], None)
    request_id = str(inner.get("sign", ""))
    return {
        "outer_code": outer.get("code"),
        "outer_message": outer.get("msg", ""),
        "status": status,
        "message": message,
        "request_id": request_id,
        "data": data,
        "is_empty": is_empty,
    }


def _normalize_search_payload(payload: dict[str, Any]) -> dict[str, Any]:
    decoded = _decode_nested_payload(payload)
    outer = decoded["outer"]
    inner = decoded["inner"] if isinstance(decoded["inner"], dict) else {}
    inner_data = inner.get("data", {})
    items = inner_data.get("items", []) if isinstance(inner_data, dict) else []
    normalized_items: list[dict[str, Any]] = []
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized_items.append(
                {
                    "name": item.get("name", ""),
                    "oper_name": item.get("oper_name", ""),
                    "credit_no": item.get("credit_no", ""),
                    "start_date": item.get("start_date", ""),
                    "reg_no": item.get("reg_no", ""),
                    "id": item.get("id", ""),
                    "match_type": item.get("matchType", ""),
                    "match_items": item.get("matchItems", ""),
                }
            )
    return {
        "outer_code": outer.get("code"),
        "outer_message": outer.get("msg", ""),
        "status": str(inner.get("status", outer.get("code", ""))),
        "message": str(inner.get("message", outer.get("msg", ""))),
        "request_id": str(inner.get("sign", "")),
        "total": inner_data.get("total", 0) if isinstance(inner_data, dict) else 0,
        "num": inner_data.get("num", len(normalized_items)) if isinstance(inner_data, dict) else len(normalized_items),
        "items": normalized_items,
        "is_empty": not normalized_items,
    }


def _normalize_balance_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw_balance = payload.get("data")
    balance = _coerce_float(raw_balance)
    state = "unknown"
    if balance is not None:
        state = "sufficient" if balance > 0 else "insufficient"
    return {
        "state": state,
        "balance": balance,
        "message": str(payload.get("msg", "")),
    }


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("balance", "money", "amount", "remain", "remaining", "quota"):
            if key in value:
                return _coerce_float(value[key])
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _render_query_markdown(
    display_name: str,
    api_id: str,
    billing: str,
    input_params: dict[str, Any],
    normalized: dict[str, Any],
) -> str:
    return (
        f"# {display_name}\n\n"
        f"- 接口 ID：`{api_id}`\n"
        f"- 计费：`{billing}`\n"
        f"- 状态：`{normalized['status']}`\n"
        f"- 消息：`{normalized['message']}`\n\n"
        "## 请求参数\n\n```json\n"
        f"{json.dumps(input_params, ensure_ascii=False, indent=2)}\n```\n\n"
        "## 返回数据\n\n```json\n"
        f"{json.dumps(normalized['data'], ensure_ascii=False, indent=2)}\n```"
    )


def _render_search_markdown(keyword: str, normalized: dict[str, Any]) -> str:
    return (
        "# 企业搜索\n\n"
        f"- 查询关键词：`{keyword}`\n"
        f"- 状态：`{normalized['status']}`\n"
        f"- 命中数：`{normalized['num']}` / `total={normalized['total']}`\n\n"
        "## 候选企业\n\n```json\n"
        f"{json.dumps(normalized['items'], ensure_ascii=False, indent=2)}\n```"
    )


def _render_balance_markdown(balance: dict[str, Any], payload: dict[str, Any]) -> str:
    return (
        "# Enterprise Balance\n\n"
        f"- 状态：`{balance['state']}`\n"
        f"- 余额：`{balance['balance']}`\n"
        f"- 说明：`{balance['message']}`\n\n"
        "## 原始返回\n\n```json\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n```"
    )
