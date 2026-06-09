import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.signals import get_rule_state_manager, router as signals_router
from app.db.database import Base, get_db
from app.models.observation import OpsEvent
from app.providers.ocs_catalog import OCSClientError
from app.providers.rule_state_manager import RuleStateManager
from app.schemas.signal_schema import RuleDiffRequest
from app.utils.oos_detector import detect_oos_conflicts
from app.utils.severity import determine_rule_severity


class FakeOCSClient:

    def __init__(self, products=None, error=False):
        self.products = products or {}
        self.error = error

    def get_product(self, product_id):
        if self.error:
            raise OCSClientError("stock lookup failed")
        return self.products.get(product_id)


def build_test_app(db_session, rules_path=None):
    test_app = FastAPI()
    test_app.include_router(signals_router, prefix="/signals")

    def override_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_db
    if rules_path is not None:

        def override_rule_state_manager():
            return RuleStateManager(rules_path)

        test_app.dependency_overrides[get_rule_state_manager] = override_rule_state_manager
    return test_app


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


@pytest.fixture()
def rules_path(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "last_updated": "2026-06-06T00:00:00Z",
                "rules": [
                    {
                        "rule_id": "MXP-001",
                        "rule_type": "boost",
                        "target_products": ["FOOT-001"],
                        "boost_factor": 1.2,
                        "active": True,
                        "created_by": "tester",
                        "created_at": "2026-06-06T00:00:00Z",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_severity_oos_conflict_is_critical():
    request = RuleDiffRequest(
        rule_id="MXP-001",
        rule_type="boost",
        operation="UPDATE",
        author="tester",
        oos_conflicts=[{"product_id": "FOOT-002", "stock": 0}],
    )

    assert determine_rule_severity(request) == "critical"


def test_severity_no_conflict_boost_update_is_warning():
    request = RuleDiffRequest(
        rule_id="MXP-001",
        rule_type="boost",
        operation="UPDATE",
        author="tester",
        oos_conflicts=[],
    )

    assert determine_rule_severity(request) == "warning"


def test_severity_delete_is_warning():
    request = RuleDiffRequest(
        rule_id="MXP-001",
        rule_type="suppress",
        operation="DELETE",
        author="tester",
        oos_conflicts=[],
    )

    assert determine_rule_severity(request) == "warning"


def test_severity_synonym_update_is_info():
    request = RuleDiffRequest(
        rule_id="MXP-001",
        rule_type="synonym",
        operation="UPDATE",
        author="tester",
        oos_conflicts=[],
    )

    assert determine_rule_severity(request) == "info"


def test_severity_activate_boost_on_oos_is_critical():
    request = RuleDiffRequest(
        rule_id="MXP-001",
        rule_type="boost",
        operation="UPDATE",
        changed_fields=["active"],
        after_state={"active": True},
        author="tester",
        oos_conflicts=[{"product_id": "ELEC-001", "stock": 0}],
    )

    assert determine_rule_severity(request) == "critical"


def test_detect_oos_conflicts_returns_oos_products():
    client = FakeOCSClient(
        {
            "FOOT-002": {"title": "Trail Shoe", "stock": 0},
            "FOOT-001": {"title": "Road Shoe", "stock": 42},
        }
    )

    result = detect_oos_conflicts(["FOOT-001", "FOOT-002"], client)

    assert result == [
        {
            "product_id": "FOOT-002",
            "title": "Trail Shoe",
            "stock": 0,
            "conflict": "rule targets out-of-stock product",
        }
    ]


def test_detect_oos_conflicts_handles_ocs_error():
    result = detect_oos_conflicts(["FOOT-001"], FakeOCSClient(error=True))

    assert result == []


def test_rule_state_manager_save_updates_existing(rules_path):
    manager = RuleStateManager(rules_path)

    rule = manager.get_rule("MXP-001")
    rule["boost_factor"] = 1.8
    manager.save_rule(rule)

    assert manager.get_rule("MXP-001")["boost_factor"] == 1.8


def test_rule_state_manager_save_appends_new(rules_path):
    manager = RuleStateManager(rules_path)

    manager.save_rule(
        {
            "rule_id": "MXP-999",
            "rule_type": "synonym",
            "target_products": [],
            "terms": ["boots"],
            "canonical": "shoes",
            "active": True,
            "created_by": "tester",
            "created_at": "2026-06-06T00:00:00Z",
        }
    )

    assert manager.get_rule("MXP-999") is not None


def test_rule_state_manager_delete_removes_rule(rules_path):
    manager = RuleStateManager(rules_path)

    assert manager.delete_rule("MXP-001") is True
    assert manager.get_rule("MXP-001") is None


def test_post_rule_diff_critical_on_oos(db_session, rules_path):
    test_app = build_test_app(db_session, rules_path)

    with TestClient(test_app) as client:
        response = client.post(
            "/signals/rule-diff",
            json={
                "rule_id": "MXP-001",
                "rule_type": "boost",
                "operation": "UPDATE",
                "changed_fields": ["boost_factor"],
                "before_state": {"boost_factor": 1.2},
                "after_state": {"boost_factor": 2.0},
                "author": "tester",
                "oos_conflicts": [{"product_id": "FOOT-002", "stock": 0}],
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "rule_diff"
    assert data["severity"] == "critical"

    event = db_session.query(OpsEvent).filter(OpsEvent.event_id == data["event_id"]).one()
    assert event.event_type == "rule_diff"
    assert event.severity == "critical"
    assert event.payload["oos_conflicts"] == [{"product_id": "FOOT-002", "stock": 0}]
    assert RuleStateManager(rules_path).get_rule("MXP-001")["boost_factor"] == 2.0


def test_post_rule_diff_warning_on_boost_update(db_session, rules_path):
    test_app = build_test_app(db_session, rules_path)

    with TestClient(test_app) as client:
        response = client.post(
            "/signals/rule-diff",
            json={
                "rule_id": "MXP-001",
                "rule_type": "boost",
                "operation": "UPDATE",
                "changed_fields": ["boost_factor"],
                "before_state": {"boost_factor": 1.2},
                "after_state": {"boost_factor": 1.8},
                "author": "tester",
                "oos_conflicts": [],
            },
        )

    assert response.status_code == 201
    assert response.json()["severity"] == "warning"
    assert RuleStateManager(rules_path).get_rule("MXP-001")["boost_factor"] == 1.8


def test_post_rule_diff_insert_and_delete_mutate_rules_json(db_session, rules_path):
    test_app = build_test_app(db_session, rules_path)

    with TestClient(test_app) as client:
        insert_response = client.post(
            "/signals/rule-diff",
            json={
                "rule_id": "MXP-999",
                "rule_type": "synonym",
                "operation": "INSERT",
                "changed_fields": ["rule_id", "rule_type", "terms", "canonical", "active"],
                "before_state": None,
                "after_state": {
                    "rule_id": "MXP-999",
                    "rule_type": "synonym",
                    "terms": ["trail runner"],
                    "canonical": "trail shoe",
                    "active": True,
                },
                "author": "tester",
                "oos_conflicts": [],
            },
        )
        delete_response = client.post(
            "/signals/rule-diff",
            json={
                "rule_id": "MXP-999",
                "rule_type": "synonym",
                "operation": "DELETE",
                "changed_fields": ["rule_id", "rule_type", "terms", "canonical", "active"],
                "before_state": {
                    "rule_id": "MXP-999",
                    "rule_type": "synonym",
                    "terms": ["trail runner"],
                    "canonical": "trail shoe",
                    "active": True,
                },
                "after_state": None,
                "author": "tester",
                "oos_conflicts": [],
            },
        )

    manager = RuleStateManager(rules_path)
    assert insert_response.status_code == 201
    assert delete_response.status_code == 201
    assert manager.get_rule("MXP-999") is None


def test_post_rule_diff_missing_required_field(db_session):
    test_app = build_test_app(db_session)

    with TestClient(test_app) as client:
        response = client.post(
            "/signals/rule-diff",
            json={
                "rule_type": "boost",
                "operation": "UPDATE",
                "author": "tester",
            },
        )

    assert response.status_code == 422


def test_post_rule_diff_invalid_rule_type(db_session):
    test_app = build_test_app(db_session)

    with TestClient(test_app) as client:
        response = client.post(
            "/signals/rule-diff",
            json={
                "rule_id": "MXP-001",
                "rule_type": "invalid",
                "operation": "UPDATE",
                "author": "tester",
            },
        )

    assert response.status_code == 422
