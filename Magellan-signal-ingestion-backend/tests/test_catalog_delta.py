import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import pytest

from app.api.signals import get_catalog_client, get_product_state_manager, router as signals_router
from app.db.database import Base, get_db
from app.models.observation import OpsEvent
from app.providers.product_state_manager import ProductStateManager
from app.schemas.signal_schema import CatalogDiffRequest
from app.utils.diff_utils import compute_diff, detect_missing_attributes
from app.utils.severity import determine_catalog_severity


class FakeCatalogClient:

    def __init__(self, fail_action=None):
        self.fail_action = fail_action
        self.actions = []

    def add_product(self, product):
        self.actions.append(("upsert", product["id"]))
        return self.fail_action != "upsert"

    def delete_product(self, product_id):
        self.actions.append(("delete", product_id))
        return self.fail_action != "delete"

    def flush_config(self):
        self.actions.append(("flush", None))
        return self.fail_action != "flush"


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
def mock_data_root(tmp_path):
    root = tmp_path / "mock-data"
    products_root = root / "products"
    products_root.mkdir(parents=True)
    (root / "index").mkdir()

    (products_root / "footwear.json").write_text(
        json.dumps(
            {
                "category": "footwear",
                "description": "Test footwear data",
                "products": [
                    {
                        "id": "FOOT-001",
                        "title": "Trail Runner",
                        "description": "Waterproof trail shoe",
                        "category": "footwear",
                        "brand": "TestBrand",
                        "price": 129,
                        "stock": 23,
                        "attributes": {
                            "waterproof": True,
                            "terrain": "trail",
                            "material": "mesh",
                            "size_range": "6-12",
                        },
                        "data_quality": "complete",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (products_root / "bags.json").write_text(
        json.dumps({"category": "bags", "description": "Test bag data", "products": []}) + "\n",
        encoding="utf-8",
    )
    (root / "index" / "product_index.json").write_text(
        json.dumps(
            {
                "description": "Flat index of all product IDs for quick lookup",
                "total": 1,
                "products": [{"id": "FOOT-001", "category": "footwear", "stock": 23, "data_quality": "complete"}],
                "oos_products": [],
                "low_stock_products": [],
                "incomplete_products": [],
                "poor_products": [],
                "new_arrivals": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return root


def build_test_app(db_session, mock_data_root=None, catalog_client=None):
    test_app = FastAPI()
    test_app.include_router(signals_router, prefix="/signals")

    def override_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_db
    if mock_data_root is not None:

        def override_product_state_manager():
            return ProductStateManager(mock_data_root)

        test_app.dependency_overrides[get_product_state_manager] = override_product_state_manager
    if catalog_client is not None:

        def override_catalog_client():
            return catalog_client

        test_app.dependency_overrides[get_catalog_client] = override_catalog_client
    return test_app


def test_severity_insert_missing_attributes():
    request = CatalogDiffRequest(
        product_id="FOOT-001",
        operation="INSERT",
        missing_attributes=["waterproof", "terrain"],
    )

    assert determine_catalog_severity(request) == "critical"


def test_severity_insert_no_missing():
    request = CatalogDiffRequest(
        product_id="FOOT-001",
        operation="INSERT",
        missing_attributes=[],
    )

    assert determine_catalog_severity(request) == "info"


def test_severity_update_embedding_sensitive():
    request = CatalogDiffRequest(
        product_id="FOOT-001",
        operation="UPDATE",
        changed_fields=["attributes.waterproof"],
    )

    assert determine_catalog_severity(request) == "warning"


def test_severity_update_non_sensitive():
    request = CatalogDiffRequest(
        product_id="FOOT-001",
        operation="UPDATE",
        changed_fields=["price"],
    )

    assert determine_catalog_severity(request) == "info"


def test_severity_delete():
    request = CatalogDiffRequest(product_id="FOOT-001", operation="DELETE")

    assert determine_catalog_severity(request) == "critical"


def test_compute_diff_detects_nulled_field():
    before = {"attributes": {"waterproof": True}}
    after = {"attributes": {"waterproof": None}}

    diff = compute_diff(before, after)

    assert diff["changed_fields"] == ["attributes.waterproof"]
    assert diff["before"] == {"attributes.waterproof": True}
    assert diff["after"] == {"attributes.waterproof": None}


def test_detect_missing_attributes_footwear():
    product = {
        "category": "footwear",
        "attributes": {"size_range": "6-12"},
    }

    result = detect_missing_attributes(product)

    assert "waterproof" in result
    assert "terrain" in result
    assert "material" in result
    assert "size_range" not in result


def test_post_catalog_diff_insert_critical(db_session, mock_data_root):
    catalog_client = FakeCatalogClient()
    test_app = build_test_app(db_session, mock_data_root, catalog_client)

    with TestClient(test_app) as client:
        response = client.post(
            "/signals/catalog-diff",
            json={
                "product_id": "BAGS-999",
                "operation": "INSERT",
                "changed_fields": [],
                "before": None,
                "after": {
                    "id": "BAGS-999",
                    "title": "Incomplete Bag",
                    "description": "Missing searchable attributes",
                    "category": "bags",
                    "brand": "TestBrand",
                    "price": 89,
                    "stock": 4,
                    "attributes": {"laptop_size": "15inch"},
                    "data_quality": "new_arrival",
                },
                "missing_attributes": ["waterproof", "terrain"],
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "catalog_delta"
    assert data["severity"] == "critical"

    event = db_session.query(OpsEvent).filter(OpsEvent.event_id == data["event_id"]).one()
    assert event.event_type == "catalog_delta"
    assert event.severity == "critical"
    assert event.payload["product_id"] == "BAGS-999"

    bags = json.loads((mock_data_root / "products" / "bags.json").read_text(encoding="utf-8"))
    index = json.loads((mock_data_root / "index" / "product_index.json").read_text(encoding="utf-8"))
    assert [product["id"] for product in bags["products"]] == ["BAGS-999"]
    assert index["total"] == 2
    assert "BAGS-999" in index["new_arrivals"]
    assert catalog_client.actions == [("upsert", "BAGS-999"), ("flush", None)]


def test_post_catalog_diff_update_warning(db_session, mock_data_root):
    catalog_client = FakeCatalogClient()
    test_app = build_test_app(db_session, mock_data_root, catalog_client)

    with TestClient(test_app) as client:
        response = client.post(
            "/signals/catalog-diff",
            json={
                "product_id": "FOOT-001",
                "operation": "UPDATE",
                "changed_fields": ["attributes.waterproof"],
                "before": {"attributes.waterproof": True},
                "after": {"attributes.waterproof": None},
                "missing_attributes": [],
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["severity"] == "warning"

    footwear = json.loads((mock_data_root / "products" / "footwear.json").read_text(encoding="utf-8"))
    assert footwear["products"][0]["attributes"]["waterproof"] is None
    assert catalog_client.actions == [("upsert", "FOOT-001"), ("flush", None)]


def test_post_catalog_diff_delete_updates_index(db_session, mock_data_root):
    catalog_client = FakeCatalogClient()
    test_app = build_test_app(db_session, mock_data_root, catalog_client)

    with TestClient(test_app) as client:
        response = client.post(
            "/signals/catalog-diff",
            json={
                "product_id": "FOOT-001",
                "operation": "DELETE",
                "changed_fields": [],
                "before": {"id": "FOOT-001"},
                "after": None,
                "missing_attributes": [],
            },
        )

    index = json.loads((mock_data_root / "index" / "product_index.json").read_text(encoding="utf-8"))
    assert response.status_code == 201
    assert response.json()["severity"] == "critical"
    assert index["total"] == 0
    assert index["products"] == []
    assert catalog_client.actions == [("delete", "FOOT-001"), ("flush", None)]


def test_post_catalog_diff_ocs_sync_failure_returns_502(db_session, mock_data_root):
    catalog_client = FakeCatalogClient(fail_action="upsert")
    test_app = build_test_app(db_session, mock_data_root, catalog_client)

    with TestClient(test_app) as client:
        response = client.post(
            "/signals/catalog-diff",
            json={
                "product_id": "FOOT-001",
                "operation": "UPDATE",
                "changed_fields": ["stock"],
                "before": {"stock": 23},
                "after": {"stock": 7},
                "missing_attributes": [],
            },
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "OCS upsert failed for FOOT-001"


def test_post_catalog_diff_missing_required_field(db_session):
    test_app = build_test_app(db_session)

    with TestClient(test_app) as client:
        response = client.post(
            "/signals/catalog-diff",
            json={
                "operation": "INSERT",
                "changed_fields": [],
                "before": None,
                "after": {},
                "missing_attributes": [],
            },
        )

    assert response.status_code == 422
