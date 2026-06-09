import asyncio
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.signals import router as signals_router
from app.db.database import Base, get_db
from app.models.observation import OpsEvent
from app.schemas.signal_schema import CatalogDeltaRequest, RuleDiffRequest, SearchSignalRequest
from app.services import ingestion_service as ingestion_module
from app.services.downstream_pipeline import DownstreamPipelineClient, build_downstream_event_payload
from app.services.ingestion_service import (
    IngestionService,
    catalog_delta_severity,
    normalize_query_intent,
    rule_diff_severity,
)


class FakeProvider:

    def __init__(self, result_count=0, status_code=200, success=True, error_type=None):
        self.result_count = result_count
        self.status_code = status_code
        self.success = success
        self.error_type = error_type
        self.last_filters = None
        self.last_sort = None

    async def search(self, query_text, tenant=None, limit=10, offset=0, filters=None, sort=None):
        self.last_filters = filters
        self.last_sort = sort
        result = {
            "provider": "ocs",
            "tenant": tenant,
            "query_text": query_text,
            "status_code": self.status_code,
            "success": self.success,
            "latency_ms": 12,
            "result_count": self.result_count,
            "top_product_ids": ["P001"] if self.result_count else [],
            "response_payload": {"slices": [{"matchCount": self.result_count, "hits": []}]},
            "metadata": {},
        }
        if self.error_type:
            result["error_type"] = self.error_type
        return result


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_normalize_query_intent_strips_stopwords():
    assert normalize_query_intent("The Waterproof Shoes for Trail") == "waterproof shoes trail"
    assert normalize_query_intent("with a laptop backpack") == "laptop backpack"


def test_zero_result_cluster_exact_match_increments(db_session):
    service = IngestionService(
        provider=FakeProvider(result_count=0),
        now_fn=lambda: datetime(2026, 6, 2, 8, 15, tzinfo=timezone.utc),
    )

    asyncio.run(service.ingest_search(db_session, SearchSignalRequest(query_text="The Waterproof Shoes")))
    asyncio.run(service.ingest_search(db_session, SearchSignalRequest(query_text="waterproof shoes for")))

    clusters = service.list_zero_result_clusters(db_session)

    assert len(clusters) == 1
    assert clusters[0].cluster_intent == "waterproof shoes"
    assert clusters[0].hit_count == 2


def test_catalog_delta_severity():
    critical = CatalogDeltaRequest(
        product_id="P001",
        operation="INSERT",
        changed_fields=[],
        before={},
        after={"title": "Shoe", "description": "Trail shoe", "category": "Footwear", "brand": "TrailMax"},
    )
    warning = CatalogDeltaRequest(
        product_id="P001",
        operation="UPDATE",
        changed_fields=["description"],
        before={"description": "Old"},
        after={"description": "New"},
    )
    critical_delete = CatalogDeltaRequest(
        product_id="P001",
        operation="DELETE",
        changed_fields=["price"],
        before={"price": 10},
        after={},
    )

    assert catalog_delta_severity(critical) == "critical"
    assert catalog_delta_severity(warning) == "warning"
    assert catalog_delta_severity(critical_delete) == "critical"


def test_rule_diff_severity():
    critical = RuleDiffRequest(
        rule_id="R001",
        rule_type="boost",
        operation="UPDATE",
        changed_fields=["boost_factor"],
        before_state={},
        after_state={"targets": [{"product_id": "P001", "stock": 0}]},
        author="tester",
        oos_conflicts=[{"product_id": "P001", "stock": 0}],
    )
    warning = RuleDiffRequest(
        rule_id="R002",
        rule_type="boost",
        operation="UPDATE",
        changed_fields=["boost_factor"],
        before_state={},
        after_state={"targets": [{"product_id": "P002", "stock": 5}]},
        author="tester",
        oos_conflicts=[],
    )

    assert rule_diff_severity(critical) == "critical"
    assert rule_diff_severity(warning) == "warning"


def test_duplicate_search_event_is_ignored(db_session):
    fixed_now = datetime(2026, 6, 2, 8, 15, 45, tzinfo=timezone.utc)
    service = IngestionService(provider=FakeProvider(result_count=4), now_fn=lambda: fixed_now)

    event_one, created_one = asyncio.run(service.ingest_search(db_session, SearchSignalRequest(query_text="office laptop")))
    event_two, created_two = asyncio.run(service.ingest_search(db_session, SearchSignalRequest(query_text="office laptop")))

    assert event_one.event_id == event_two.event_id
    assert created_one is True
    assert created_two is False
    assert len(service.list_events(db_session)) == 1


def test_search_sanitizes_swagger_placeholders(db_session):
    provider = FakeProvider(result_count=4)
    service = IngestionService(provider=provider)

    event, created = asyncio.run(
        service.ingest_search(
            db_session,
            SearchSignalRequest(
                query_text="bike",
                filters={"additionalProp1": {}, "brand": ""},
                sort="string",
            ),
        )
    )

    assert created is True
    assert provider.last_filters == {}
    assert provider.last_sort is None
    assert event.payload["filters"] == {}
    assert "sort" not in event.payload


def test_signals_search_route_persists_event(db_session, monkeypatch):
    test_app = FastAPI()
    test_app.include_router(signals_router, prefix="/signals")

    def override_db():
        yield db_session

    monkeypatch.setattr(ingestion_module, "get_search_provider", lambda: FakeProvider(result_count=2))
    test_app.dependency_overrides[get_db] = override_db

    with TestClient(test_app) as client:
        response = client.post("/signals/search", json={"query_text": "office laptop"})

    assert response.status_code == 200
    data = response.json()
    assert data["event_type"] == "search_result"
    assert data["severity"] == "info"
    assert data["payload"]["result_count"] == 2


def test_downstream_event_payload_uses_event_id_as_idempotency_key():
    timestamp = datetime(2026, 6, 2, 8, 15, tzinfo=timezone.utc)
    event = OpsEvent(
        event_id="SR-20260602-test",
        event_type="search_result",
        source_capability="semantic_search",
        severity="warning",
        timestamp=timestamp,
        ingested_at=timestamp,
        provider="ocs",
        tenant="ocs_example",
        payload={"query_text": "waterproof shoes", "result_count": 0},
    )

    payload = build_downstream_event_payload(event)

    assert payload["idempotency_key"] == "SR-20260602-test"
    assert payload["event_id"] == "SR-20260602-test"
    assert payload["event_type"] == "search_result"
    assert payload["severity"] == "warning"
    assert payload["payload"]["result_count"] == 0


def test_downstream_pipeline_client_noops_without_url():
    client = DownstreamPipelineClient(base_url="", enabled=True)

    assert client.dispatch_event_payload({"event_id": "SR-20260602-test"}) is False
