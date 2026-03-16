from __future__ import annotations

import re
from typing import Any, Callable

from metainflow_studio_cli.core.errors import ValidationError
from metainflow_studio_cli.services.enterprise_query.service import enterprise_query, enterprise_search


COMPANY_SUFFIXES = (
    "有限公司",
    "有限责任公司",
    "股份有限公司",
    "集团有限公司",
    "集团股份有限公司",
    "合伙企业",
    "有限合伙",
    "事务所",
    "研究院",
    "合作社",
)
REFRESH_HINTS = ("重新查", "最新", "别用缓存", "刷新", "重新查询", "实时")
_CREDIT_CODE_RE = re.compile(r"^[0-9A-Z]{18}$")
_REG_NO_RE = re.compile(r"^(?=.*\d)[0-9A-Z-]{8,}$")


def detect_identifier_kind(identifier: str) -> str:
    normalized = identifier.strip()
    if not normalized:
        raise ValidationError("enterprise identifier must not be empty")
    upper = normalized.upper()
    if _CREDIT_CODE_RE.fullmatch(upper):
        return "credit-code"
    if _REG_NO_RE.fullmatch(upper) and not _contains_chinese(normalized):
        return "registration-number"
    if _looks_like_full_company_name(normalized):
        return "full-name"
    return "ambiguous"


def should_refresh_from_text(intent_text: str) -> bool:
    normalized = intent_text.strip()
    return any(token in normalized for token in REFRESH_HINTS)


def route_enterprise_query(
    identifier: str,
    query_type: str,
    intent_text: str = "",
    session_id: str = "",
    refresh: bool = False,
    exact_query_fn: Callable[..., dict[str, Any]] = enterprise_query,
    search_query_fn: Callable[..., dict[str, Any]] = enterprise_search,
) -> dict[str, Any]:
    identifier_kind = detect_identifier_kind(identifier)
    effective_refresh = refresh or should_refresh_from_text(intent_text)

    if identifier_kind in {"credit-code", "registration-number"}:
        exact = exact_query_fn(query_type=query_type, keyword=identifier, output="json", session_id=session_id, refresh=effective_refresh)
        return _exact_route_response("exact", identifier_kind, exact)

    if identifier_kind == "full-name":
        exact = exact_query_fn(query_type=query_type, keyword=identifier, output="json", session_id=session_id, refresh=effective_refresh)
        if not exact["data"]["is_empty"]:
            return _exact_route_response("exact", identifier_kind, exact)
        search = search_query_fn(keyword=identifier, output="json", session_id=session_id, refresh=effective_refresh)
        return _search_route_response("exact->fuzzy fallback", identifier_kind, search)

    search = search_query_fn(keyword=identifier, output="json", session_id=session_id, refresh=effective_refresh)
    candidates = search["data"]["candidates"]
    if len(candidates) == 1:
        resolved = candidates[0]
        exact = exact_query_fn(
            query_type=query_type,
            keyword=resolved["credit_no"] or resolved["name"],
            output="json",
            session_id=session_id,
            refresh=effective_refresh,
        )
        result = _exact_route_response("fuzzy", identifier_kind, exact)
        result["data"]["resolved_candidate"] = resolved
        result["data"]["search_cache_hit"] = search["meta"]["cache_hit"]
        return result
    return _search_route_response("fuzzy", identifier_kind, search)


def _exact_route_response(route: str, identifier_kind: str, exact: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": True,
        "data": {
            "route": route,
            "identifier_kind": identifier_kind,
            "requires_confirmation": False,
            "candidates": [],
            "result": exact,
            "cache_hit": exact["meta"]["cache_hit"],
        },
        "error": None,
    }


def _search_route_response(route: str, identifier_kind: str, search: dict[str, Any]) -> dict[str, Any]:
    candidates = search["data"]["candidates"]
    requires_confirmation = len(candidates) > 1
    return {
        "success": True,
        "data": {
            "route": route,
            "identifier_kind": identifier_kind,
            "requires_confirmation": requires_confirmation,
            "candidates": _compact_candidates(candidates),
            "result": None if requires_confirmation or search["data"]["is_empty"] else search,
            "cache_hit": search["meta"]["cache_hit"],
        },
        "error": None,
    }


def _compact_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for item in candidates:
        compact.append(
            {
                "name": item.get("name", ""),
                "oper_name": item.get("oper_name", ""),
                "credit_no": item.get("credit_no", ""),
                "start_date": item.get("start_date", ""),
            }
        )
    return compact


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _looks_like_full_company_name(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 6:
        return False
    return any(stripped.endswith(suffix) for suffix in COMPANY_SUFFIXES)
