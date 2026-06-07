#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.diff_utils import compute_diff, detect_missing_attributes  # noqa: E402

MAGELLAN_URL = "http://127.0.0.1:8000"
MOCK_DATA_ROOT = PROJECT_ROOT / "mock-data"

logger = logging.getLogger("catalog_delta_simulator")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_product(product_id: str, source_file: str) -> Dict[str, Any]:
    product_file = MOCK_DATA_ROOT / source_file
    payload = read_json(product_file)
    for product in payload.get("products", []):
        if product.get("id") == product_id:
            return product
    raise ValueError(f"Product {product_id} not found in {source_file}")


def apply_scenario_changes(product: Dict[str, Any], changes: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    updated = copy.deepcopy(product)
    for field_path, change in changes.items():
        set_dot_path(updated, field_path, change.get("after"))
    return updated


def set_dot_path(payload: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current = payload
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    current[parts[-1]] = value


def post_catalog_diff(signal: Dict[str, Any]) -> Optional[str]:
    try:
        with httpx.Client(base_url=MAGELLAN_URL, timeout=10.0) as client:
            response = client.post("/signals/catalog-diff", json=signal)
    except httpx.RequestError as exc:
        logger.warning("Magellan catalog-diff POST failed for %s: %s", signal["product_id"], exc)
        return None

    if response.status_code != 201:
        logger.warning(
            "Magellan catalog-diff POST returned %s for %s: %s",
            response.status_code,
            signal["product_id"],
            response.text,
        )
        return None

    payload = response.json()
    return payload.get("severity")


def simulate_insert(scenario: Dict[str, Any]) -> Optional[str]:
    product_id = scenario["product_id"]
    product = load_product(product_id, scenario["source_file"])
    signal = {
        "product_id": product_id,
        "operation": "INSERT",
        "changed_fields": [],
        "before": None,
        "after": product,
        "missing_attributes": detect_missing_attributes(product),
    }
    return post_catalog_diff(signal)


def simulate_update(scenario: Dict[str, Any]) -> Optional[str]:
    product_id = scenario["product_id"]
    before = load_product(product_id, scenario["source_file"])

    changes = scenario.get("changes") or {}
    after = apply_scenario_changes(before, changes)
    diff = compute_diff(before, after)
    signal = {
        "product_id": product_id,
        "operation": "UPDATE",
        "changed_fields": diff["changed_fields"],
        "before": diff["before"],
        "after": diff["after"],
        "missing_attributes": detect_missing_attributes(after),
    }
    return post_catalog_diff(signal)


def simulate_delete(scenario: Dict[str, Any]) -> Optional[str]:
    product_id = scenario["product_id"]
    before = load_product(product_id, scenario["source_file"])

    signal = {
        "product_id": product_id,
        "operation": "DELETE",
        "changed_fields": [],
        "before": before,
        "after": None,
        "missing_attributes": [],
    }
    return post_catalog_diff(signal)


def simulate_scenario(scenario: Dict[str, Any]) -> Optional[str]:
    operation = scenario["operation"].upper()
    if operation == "INSERT":
        return simulate_insert(scenario)
    if operation == "UPDATE":
        return simulate_update(scenario)
    if operation == "DELETE":
        return simulate_delete(scenario)
    logger.warning("Skipping unsupported operation %s for %s", operation, scenario.get("product_id"))
    return None


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    scenarios = read_json(MOCK_DATA_ROOT / "scenarios" / "catalog_scenarios.json")["scenarios"]
    read_json(MOCK_DATA_ROOT / "index" / "product_index.json")

    succeeded = 0
    failed = 0
    by_severity: Counter[str] = Counter()

    for scenario in scenarios:
        try:
            severity = simulate_scenario(scenario)
        except Exception:
            logger.exception("Skipping %s after unexpected error", scenario.get("name"))
            severity = None

        if severity:
            succeeded += 1
            by_severity[severity] += 1
        else:
            failed += 1

    print(
        json.dumps(
            {
                "total_scenarios": len(scenarios),
                "succeeded": succeeded,
                "failed": failed,
                "by_severity": dict(by_severity),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    run()
