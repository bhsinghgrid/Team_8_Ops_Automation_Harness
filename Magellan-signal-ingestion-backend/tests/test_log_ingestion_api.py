import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.log_ingestion import router as logs_router
from app.db.database import Base, get_db
from app.models.observation import SearchLog, OpsEvent
from app.core import detection_config

@pytest.fixture()
def client_and_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    test_app = FastAPI()
    test_app.include_router(logs_router)

    def override_db():
        yield db

    test_app.dependency_overrides[get_db] = override_db

    with TestClient(test_app) as client:
        yield client, db

    db.close()
    Base.metadata.drop_all(bind=engine)


def test_ingest_single_log(client_and_db):
    client, db = client_and_db
    payload = {
        "timestamp": "2026-06-06T10:15:30Z",
        "source": "gd_ai_search",
        "tenant": "t1",
        "request_id": "req_single_1",
        "session_id": "sess_1",
        "user_id_hash": "u1",
        "query": {
            "text": "shoes",
            "normalized_text": "shoes",
            "filters": {},
            "sort": None
        },
        "response": {
            "status_code": 200,
            "latency_ms": 50,
            "result_count": 5,
            "results": [{"product_id": "P1", "rank": 1, "score": 0.9}]
        },
        "interaction": {"clicks": [], "cart_adds": []},
        "context": {"device_type": "desktop", "channel": "web", "locale": "en-US"},
        "error": None
    }
    response = client.post("/ingest", json=payload)
    assert response.status_code == 200
    assert response.json() == []  # no signal because sample size < 10

    # Verify raw log got saved in DB
    raw_log = db.query(SearchLog).filter(SearchLog.request_id == "req_single_1").first()
    assert raw_log is not None
    assert raw_log.query_text == "shoes"
    assert raw_log.click_count == 0


def test_ingest_batch_triggers_alert(client_and_db):
    client, db = client_and_db
    # Create 10 logs with 20% zero results rate (exceeds warning threshold of 10% for sample size >= 10)
    logs = []
    for i in range(8):
        logs.append({
            "timestamp": "2026-06-06T10:15:30Z",
            "source": "gd_ai_search",
            "tenant": "ocs_example",
            "request_id": f"req_batch_{i}",
            "session_id": "sess_1",
            "user_id_hash": "u1",
            "query": {"text": "shoes", "normalized_text": "shoes", "filters": {}, "sort": None},
            "response": {
                "status_code": 200,
                "latency_ms": 50,
                "result_count": 5,
                "results": [{"product_id": f"P{i}", "rank": 1, "score": 0.9}]
            },
            "interaction": {
                "clicks": [{"product_id": f"P{i}", "rank": 1, "timestamp": "2026-06-06T10:15:45Z"}],
                "cart_adds": []
            },
            "context": {"device_type": "desktop", "channel": "web", "locale": "en-US"},
            "error": None
        })
    for i in range(8, 10):
        logs.append({
            "timestamp": "2026-06-06T10:15:30Z",
            "source": "gd_ai_search",
            "tenant": "ocs_example",
            "request_id": f"req_batch_{i}",
            "session_id": "sess_1",
            "user_id_hash": "u1",
            "query": {"text": "empty_query", "normalized_text": "empty", "filters": {}, "sort": None},
            "response": {
                "status_code": 200,
                "latency_ms": 50,
                "result_count": 0,
                "results": []
            },
            "interaction": {"clicks": [], "cart_adds": []},
            "context": {"device_type": "desktop", "channel": "web", "locale": "en-US"},
            "error": None
        })

    response = client.post("/ingest/batch", json={"logs": logs})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["ingested_logs"] == 10
    assert data["detected_signals_count"] == 1
    assert data["signals"][0]["signal_type"] == "zero_results"
    assert data["signals"][0]["severity"] == "warning"

    # Verify signals API
    sig_response = client.get("/signals")
    assert sig_response.status_code == 200
    signals = sig_response.json()
    assert len(signals) == 1
    assert signals[0]["signal_type"] == "zero_results"

    # Verify stats API
    stats_response = client.get("/stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["total_logs"] == 10
    assert stats["avg_latency_ms"] == 50.0
    assert stats["ctr"] == 1.0  # 8 clicked searches / 8 searches with results


def test_ingest_file_not_found(client_and_db):
    client, db = client_and_db
    response = client.post("/ingest/file", json={"file_path": "nonexistent_file.jsonl"})
    assert response.status_code == 404


def test_end_to_end_ingestion_from_generated_file(client_and_db, tmp_path):
    client, db = client_and_db
    
    # 1. Generate mock data into a temporary directory
    mock_data_dir = tmp_path / "mock_data"
    mock_data_dir.mkdir()
    # Ugly path hack to make generate findable. In a real package it'd be installed.
    import sys
    from pathlib import Path
    script_path = Path(__file__).resolve().parents[1] / "scripts"
    sys.path.append(str(script_path))
    from generate_mock_data import generate
    generate(mock_data_dir)
    sys.path.pop()

    log_file_path = mock_data_dir / "logs" / "search_events.jsonl"
    assert log_file_path.exists()

    # Monkeypatch config to ensure all signals fire with mock data
    from app.core import detection_config
    original_config = detection_config.DETECTION_DEFAULTS.copy()
    detection_config.DETECTION_DEFAULTS["low_ctr"]["rate_warning"] = 0.10
    detection_config.DETECTION_DEFAULTS["low_ctr"]["min_sample_size"] = 10

    try:
        # 2. Call the /ingest/file endpoint
        response = client.post("/ingest/file", json={"file_path": str(log_file_path)})
        assert response.status_code == 200
        data = response.json()

        # 3. Verify the response
        assert data["status"] == "success"
        assert data["parsed_successfully"] == 500
        assert data["failed_parsing"] == 0
        assert data["ingested_logs"] == 500
        assert data["detected_signals_count"] > 0

        # 4. Verify signals were persisted in the database
        signals = db.query(OpsEvent).all()
        assert len(signals) == data["detected_signals_count"]
        
        # Check for specific signal types
        signal_types = {s.payload["signal_type"] for s in signals}
        assert "latency_spike" in signal_types
        assert "zero_results" in signal_types
        assert "low_ctr" in signal_types
        assert "error_rate" in signal_types
    finally:
        # Restore original config
        detection_config.DETECTION_DEFAULTS = original_config

