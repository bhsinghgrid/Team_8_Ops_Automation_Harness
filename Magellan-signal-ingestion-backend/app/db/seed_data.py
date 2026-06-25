from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.observation import MerchandisingRule, Product

DEFAULT_MOCK_DATA_ROOT = Path(__file__).resolve().parents[2] / "mock-data"


def seed_state_from_fixtures(db: Session, mock_data_root: Path = DEFAULT_MOCK_DATA_ROOT) -> Dict[str, int]:
    return {
        "products": seed_products_from_fixtures(db, mock_data_root),
        "rules": seed_rules_from_fixtures(db, mock_data_root),
    }


def seed_products_from_fixtures(db: Session, mock_data_root: Path = DEFAULT_MOCK_DATA_ROOT) -> int:
    if db.query(Product).first() is not None:
        return 0

    products_root = mock_data_root / "products"
    if not products_root.exists():
        return 0

    count = 0
    now = datetime.now(timezone.utc)
    for path in sorted(products_root.glob("*.json")):
        payload = _read_json(path)
        for product in payload.get("products", []):
            product_id = product.get("id")
            category = str(product.get("category") or payload.get("category") or path.stem).lower()
            if not product_id or not category:
                continue
            db.add(
                Product(
                    id=str(product_id),
                    category=category,
                    payload=product,
                    updated_at=now,
                )
            )
            count += 1

    db.commit()
    return count


def seed_rules_from_fixtures(db: Session, mock_data_root: Path = DEFAULT_MOCK_DATA_ROOT) -> int:
    if db.query(MerchandisingRule).first() is not None:
        return 0

    rules_path = mock_data_root / "rules" / "rules.json"
    if not rules_path.exists():
        return 0

    count = 0
    now = datetime.now(timezone.utc)
    payload = _read_json(rules_path)
    for rule in payload.get("rules", []):
        rule_id = rule.get("rule_id")
        rule_type = rule.get("rule_type")
        if not rule_id or not rule_type:
            continue
        db.add(
            MerchandisingRule(
                rule_id=str(rule_id),
                rule_type=str(rule_type),
                active=bool(rule.get("active", False)),
                payload=rule,
                updated_at=now,
            )
        )
        count += 1

    db.commit()
    return count


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
