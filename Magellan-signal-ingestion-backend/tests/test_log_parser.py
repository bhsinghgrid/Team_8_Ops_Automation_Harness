import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from app.services.log_parser import parse_log_line, parse_log_batch, LogParseError


def test_parse_valid_nested_log():
    nested_json = """{
        "timestamp": "2026-06-06T10:15:30Z",
        "source": "gd_ai_search",
        "tenant": "retail_tenant_001",
        "request_id": "req_9f82a1",
        "session_id": "sess_42ab",
        "user_id_hash": "usr_7d91",
        "query": {
            "text": "waterproof trail shoe",
            "normalized_text": "waterproof trail shoes",
            "filters": {
                "category": "Footwear"
            },
            "sort": "relevance"
        },
        "response": {
            "status_code": 200,
            "latency_ms": 42,
            "result_count": 1,
            "results": [
                {
                    "product_id": "FOOT-001",
                    "rank": 1,
                    "score": 0.94
                }
            ]
        },
        "interaction": {
            "clicks": [
                {
                    "product_id": "FOOT-001",
                    "rank": 1,
                    "timestamp": "2026-06-06T10:15:45Z"
                }
            ],
            "cart_adds": []
        },
        "context": {
            "device_type": "desktop",
            "channel": "web",
            "locale": "en-US"
        },
        "error": null
    }"""
    entry = parse_log_line(nested_json)
    assert entry.request_id == "req_9f82a1"
    assert entry.query.text == "waterproof trail shoe"
    assert entry.response.latency_ms == 42
    assert entry.response.results[0].product_id == "FOOT-001"
    assert entry.interaction.clicks[0].product_id == "FOOT-001"


def test_parse_legacy_flat_log():
    legacy_json = """{
        "timestamp": "2026-06-06T10:15:30Z",
        "source": "legacy_web_search",
        "tenant": "retail_tenant_001",
        "request_id": "req_flat_001",
        "session_id": "sess_42ab",
        "user_id_hash": "usr_7d91",
        "query_text": "waterproof trail shoe",
        "status_code": 200,
        "latency_ms": 42,
        "result_count": 12,
        "top_product_ids": ["FOOT-001", "FOOT-007"],
        "clicked_product_ids": ["FOOT-001"],
        "cart_add_product_ids": [],
        "filters": {"category": "Footwear"},
        "sort": "relevance",
        "device_type": "desktop",
        "channel": "web",
        "locale": "en-US"
    }"""
    entry = parse_log_line(legacy_json)
    assert entry.request_id == "req_flat_001"
    assert entry.query.text == "waterproof trail shoe"
    assert entry.query.normalized_text == "waterproof trail shoe"  # normalized automatically
    assert entry.response.status_code == 200
    assert entry.response.latency_ms == 42
    assert len(entry.response.results) == 2
    assert entry.response.results[0].product_id == "FOOT-001"
    assert entry.response.results[0].rank == 1
    assert len(entry.interaction.clicks) == 1
    assert entry.interaction.clicks[0].product_id == "FOOT-001"
    assert entry.interaction.clicks[0].rank == 1
    assert entry.context.device_type == "desktop"


def test_parse_invalid_log_raises_error():
    with pytest.raises(LogParseError):
        parse_log_line("not-json")

    with pytest.raises(LogParseError):
        # Missing required fields in both legacy and nested formats
        parse_log_line('{"some_key": "some_value"}')


def test_parse_log_batch():
    lines = [
        '{"timestamp": "2026-06-06T10:15:30Z", "source": "gd", "tenant": "t1", "request_id": "req1", "session_id": "s1", "user_id_hash": "u1", "query_text": "shoes", "status_code": 200, "latency_ms": 10, "result_count": 1}',
        'invalid line',
        '{"timestamp": "2026-06-06T10:15:30Z", "source": "gd", "tenant": "t1", "request_id": "req2", "session_id": "s1", "user_id_hash": "u1", "query_text": "boots", "status_code": 200, "latency_ms": 20, "result_count": 1}'
    ]
    successes, errors = parse_log_batch(lines)
    assert len(successes) == 2
    assert len(errors) == 1
    assert successes[0].request_id == "req1"
    assert successes[1].request_id == "req2"
    assert errors[0]["line_number"] == 2
