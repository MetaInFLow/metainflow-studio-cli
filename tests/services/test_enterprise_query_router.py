from metainflow_studio_cli.services.enterprise_query.router import (
    detect_identifier_kind,
    route_enterprise_query,
    should_refresh_from_text,
)


def test_detect_identifier_kind_prefers_credit_code() -> None:
    assert detect_identifier_kind("91310000MA1234567X") == "credit-code"


def test_detect_identifier_kind_for_full_company_name() -> None:
    assert detect_identifier_kind("示例智能（深圳）科技有限公司") == "full-name"


def test_detect_identifier_kind_for_fragment() -> None:
    assert detect_identifier_kind("示例智能") == "ambiguous"


def test_should_refresh_from_text() -> None:
    assert should_refresh_from_text("帮我最新重新查一下")


def test_route_full_name_uses_exact_first() -> None:
    calls: list[str] = []

    def fake_exact_query(**kwargs):
        calls.append("exact")
        return {
            "success": True,
            "data": {"is_empty": False},
            "meta": {"cache_hit": False},
            "error": None,
        }

    def fake_search_query(**kwargs):
        calls.append("search")
        raise AssertionError("should not search")

    result = route_enterprise_query(
        identifier="示例智能（深圳）科技有限公司",
        query_type="business",
        exact_query_fn=fake_exact_query,
        search_query_fn=fake_search_query,
    )
    assert calls == ["exact"]
    assert result["data"]["route"] == "exact"


def test_route_exact_fallbacks_to_search() -> None:
    calls: list[str] = []

    def fake_exact_query(**kwargs):
        calls.append("exact")
        return {
            "success": True,
            "data": {"is_empty": True},
            "meta": {"cache_hit": False},
            "error": None,
        }

    def fake_search_query(**kwargs):
        calls.append("search")
        return {
            "success": True,
            "data": {
                "is_empty": False,
                "candidates": [
                    {"name": "A", "oper_name": "B", "credit_no": "C", "start_date": "D"},
                    {"name": "E", "oper_name": "F", "credit_no": "G", "start_date": "H"},
                ],
            },
            "meta": {"cache_hit": False},
            "error": None,
        }

    result = route_enterprise_query(
        identifier="示例智能（深圳）科技有限公司",
        query_type="business",
        exact_query_fn=fake_exact_query,
        search_query_fn=fake_search_query,
    )
    assert calls == ["exact", "search"]
    assert result["data"]["route"] == "exact->fuzzy fallback"
    assert result["data"]["requires_confirmation"] is True


def test_route_fragment_uses_search_and_requires_confirmation() -> None:
    def fake_search_query(**kwargs):
        return {
            "success": True,
            "data": {
                "is_empty": False,
                "candidates": [
                    {"name": "A", "oper_name": "B", "credit_no": "C", "start_date": "D"},
                    {"name": "E", "oper_name": "F", "credit_no": "G", "start_date": "H"},
                ],
            },
            "meta": {"cache_hit": True},
            "error": None,
        }

    result = route_enterprise_query(
        identifier="示例智能",
        query_type="business",
        search_query_fn=fake_search_query,
    )
    assert result["data"]["route"] == "fuzzy"
    assert result["data"]["requires_confirmation"] is True
    assert len(result["data"]["candidates"]) == 2


def test_route_single_fuzzy_candidate_continues_to_exact() -> None:
    def fake_search_query(**kwargs):
        return {
            "success": True,
            "data": {
                "is_empty": False,
                "candidates": [
                    {"name": "示例智能（深圳）科技有限公司", "oper_name": "张三", "credit_no": "91310000MA1234567X", "start_date": "2024-09-14"},
                ],
            },
            "meta": {"cache_hit": False},
            "error": None,
        }

    def fake_exact_query(**kwargs):
        assert kwargs["keyword"] == "91310000MA1234567X"
        return {
            "success": True,
            "data": {"is_empty": False},
            "meta": {"cache_hit": False},
            "error": None,
        }

    result = route_enterprise_query(
        identifier="示例智能",
        query_type="business",
        exact_query_fn=fake_exact_query,
        search_query_fn=fake_search_query,
    )
    assert result["data"]["route"] == "fuzzy"
    assert result["data"]["requires_confirmation"] is False
