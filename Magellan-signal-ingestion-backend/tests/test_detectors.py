import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timezone
from typing import List
import pytest

from app.schemas.search_log_schema import SearchLogEntry, QueryBlock, ResponseBlock, InteractionBlock, ContextBlock
from app.services.detectors.latency_detector import LatencyDetector
from app.services.detectors.zero_result_detector import ZeroResultDetector
from app.services.detectors.ctr_detector import CtrDetector
from app.services.detectors.error_detector import ErrorDetector
from app.services.detectors.relevance_detector import RelevanceDetector


def make_mock_log(
    latency: int = 100,
    status_code: int = 200,
    result_count: int = 5,
    query_text: str = "hiking shoes",
    clicks_count: int = 1,
    avg_score: float = 0.8,
    error: str = None,
    timestamp: datetime = None
) -> SearchLogEntry:
    timestamp = timestamp or datetime.now(timezone.utc)
    
    results = [
        {"product_id": f"P{i}", "rank": i + 1, "score": avg_score}
        for i in range(result_count)
    ]
    
    clicks = [
        {"product_id": "P0", "rank": 1, "timestamp": timestamp}
        for _ in range(clicks_count)
    ]
    
    return SearchLogEntry(
        timestamp=timestamp,
        source="test",
        tenant="test_tenant",
        request_id=f"req_{timestamp.timestamp()}_{clicks_count}_{latency}",
        session_id="sess_1",
        user_id_hash="user_hash",
        query=QueryBlock(text=query_text, normalized_text=query_text, filters={}, sort=None),
        response=ResponseBlock(status_code=status_code, latency_ms=latency, result_count=result_count, results=results),
        interaction=InteractionBlock(clicks=clicks, cart_adds=[]),
        context=ContextBlock(device_type="desktop", channel="web", locale="en-US"),
        error=error
    )


def test_latency_detector():
    detector = LatencyDetector({
        "p95_warning_ms": 500,
        "p95_critical_ms": 1000,
    })
    window_start = datetime.now(timezone.utc)
    window_end = datetime.now(timezone.utc)

    # 1. Normal latency
    logs = [make_mock_log(latency=100) for _ in range(10)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 0

    # 2. Warning latency (P95 exceeds 500ms)
    # 9 logs at 100ms, 1 log at 600ms -> P95 is 600ms
    logs = [make_mock_log(latency=100) for _ in range(9)] + [make_mock_log(latency=600)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 1
    assert signals[0].severity == "warning"
    assert signals[0].evidence["p95_latency_ms"] == 600

    # 3. Critical latency (P95 exceeds 1000ms)
    logs = [make_mock_log(latency=100) for _ in range(9)] + [make_mock_log(latency=1200)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 1
    assert signals[0].severity == "critical"
    assert signals[0].evidence["p95_latency_ms"] == 1200


def test_zero_result_detector():
    detector = ZeroResultDetector({
        "rate_warning": 0.10,
        "rate_critical": 0.25,
        "min_sample_size": 10
    })
    window_start = datetime.now(timezone.utc)
    window_end = datetime.now(timezone.utc)

    # 1. Below min sample size
    logs = [make_mock_log(result_count=0) for _ in range(5)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 0

    # 2. Normal (0% zero results)
    logs = [make_mock_log(result_count=5) for _ in range(10)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 0

    # 3. Warning (20% zero results, exceeds 10%)
    logs = [make_mock_log(result_count=5) for _ in range(8)] + [make_mock_log(result_count=0) for _ in range(2)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 1
    assert signals[0].severity == "warning"
    assert signals[0].evidence["zero_result_count"] == 2

    # 4. Critical (30% zero results, exceeds 25%)
    logs = [make_mock_log(result_count=5) for _ in range(7)] + [make_mock_log(result_count=0) for _ in range(3)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 1
    assert signals[0].severity == "critical"


def test_ctr_detector():
    detector = CtrDetector({
        "rate_warning": 0.05,
        "rate_critical": 0.02,
        "min_sample_size": 20
    })
    window_start = datetime.now(timezone.utc)
    window_end = datetime.now(timezone.utc)

    # 1. Normal (100% CTR)
    logs = [make_mock_log(clicks_count=1) for _ in range(20)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 0

    # 2. Warning (4% CTR, falls below 5%)
    # 24 logs with 0 clicks, 1 log with 1 click -> CTR = 1/25 = 4%
    logs = [make_mock_log(clicks_count=0) for _ in range(24)] + [make_mock_log(clicks_count=1)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 1
    assert signals[0].severity == "warning"
    assert signals[0].evidence["ctr"] == 0.04

    # 3. Critical (0% CTR, falls below 2%)
    logs = [make_mock_log(clicks_count=0) for _ in range(20)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 1
    assert signals[0].severity == "critical"


def test_error_detector():
    detector = ErrorDetector({
        "rate_warning": 0.01,
        "rate_critical": 0.05,
        "min_sample_size": 10
    })
    window_start = datetime.now(timezone.utc)
    window_end = datetime.now(timezone.utc)

    # 1. Normal
    logs = [make_mock_log(status_code=200) for _ in range(10)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 0

    # 2. Warning (2% error rate, exceeds 1%)
    # 98 logs at 200, 2 logs at 500
    logs = [make_mock_log(status_code=200) for _ in range(98)] + [make_mock_log(status_code=500) for _ in range(2)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 1
    assert signals[0].severity == "warning"

    # 3. Critical (10% error rate, exceeds 5%)
    logs = [make_mock_log(status_code=200) for _ in range(9)] + [make_mock_log(status_code=500)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 1
    assert signals[0].severity == "critical"


def test_relevance_detector():
    detector = RelevanceDetector({
        "avg_score_warning": 0.5,
        "avg_score_critical": 0.3,
        "min_sample_size": 10
    })
    window_start = datetime.now(timezone.utc)
    window_end = datetime.now(timezone.utc)

    # 1. Normal
    logs = [make_mock_log(avg_score=0.8) for _ in range(10)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 0

    # 2. Warning (falls below 0.5)
    logs = [make_mock_log(avg_score=0.45) for _ in range(10)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 1
    assert signals[0].severity == "warning"

    # 3. Critical (falls below 0.3)
    logs = [make_mock_log(avg_score=0.2) for _ in range(10)]
    signals = detector.detect(logs, window_start, window_end)
    assert len(signals) == 1
    assert signals[0].severity == "critical"
