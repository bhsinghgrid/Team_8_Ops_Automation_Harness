#!/usr/bin/env python3
from __future__ import annotations

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

from app.core.config import settings  # noqa: E402
from app.providers.ocs_catalog import OCSCatalogClient  # noqa: E402
from app.providers.rule_state_manager import RuleStateManager  # noqa: E402
from app.utils.oos_detector import detect_oos_conflicts  # noqa: E402

MAGELLAN_URL = settings.MAGELLAN_API_URL.rstrip("/")
MOCK_DATA_ROOT = PROJECT_ROOT / "mock-data"

logger = logging.getLogger("rule_diff_simulator")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def post_rule_diff(signal: Dict[str, Any]) -> Optional[str]:
    try:
        with httpx.Client(base_url=MAGELLAN_URL, timeout=10.0) as client:
            response = client.post("/signals/rule-diff", json=signal)
    except httpx.RequestError as exc:
        logger.warning("Magellan rule-diff POST failed for %s: %s", signal["rule_id"], exc)
        return None

    if response.status_code != 201:
        logger.warning(
            "Magellan rule-diff POST returned %s for %s: %s",
            response.status_code,
            signal["rule_id"],
            response.text,
        )
        return None

    payload = response.json()
    return payload.get("severity")


def scenario_author(rule: Dict[str, Any]) -> str:
    return str(rule.get("created_by") or rule.get("author") or "rule_simulator")


def changed_fields_from_changes(changes: Dict[str, Dict[str, Any]]) -> list[str]:
    return list(changes.keys())


def simulate_insert(
    scenario: Dict[str, Any],
    ocs_client: OCSCatalogClient,
) -> Optional[str]:
    after_state = scenario["rule"]
    target_products = after_state.get("target_products", [])
    signal = {
        "rule_id": scenario["rule_id"],
        "rule_type": after_state["rule_type"],
        "operation": "INSERT",
        "changed_fields": list(after_state.keys()),
        "before_state": None,
        "after_state": after_state,
        "author": scenario_author(after_state),
        "oos_conflicts": detect_oos_conflicts(target_products, ocs_client),
    }
    return post_rule_diff(signal)


def simulate_update(
    scenario: Dict[str, Any],
    ocs_client: OCSCatalogClient,
    rule_state: RuleStateManager,
) -> Optional[str]:
    existing = rule_state.get_rule(scenario["rule_id"])
    if existing is None:
        logger.warning("Skipping UPDATE %s because rule was not found", scenario["rule_id"])
        return None

    changes = scenario.get("changes") or {}
    changed_fields = changed_fields_from_changes(changes)
    before_state = {field: existing.get(field) for field in changed_fields}
    after_state = {field: changes[field].get("after") for field in changed_fields}
    target_products = after_state.get("target_products") if "target_products" in changed_fields else existing.get("target_products", [])
    signal = {
        "rule_id": scenario["rule_id"],
        "rule_type": existing["rule_type"],
        "operation": "UPDATE",
        "changed_fields": changed_fields,
        "before_state": before_state,
        "after_state": after_state,
        "author": scenario_author(existing),
        "oos_conflicts": detect_oos_conflicts(target_products or [], ocs_client),
    }
    return post_rule_diff(signal)


def simulate_delete(scenario: Dict[str, Any], rule_state: RuleStateManager) -> Optional[str]:
    existing = rule_state.get_rule(scenario["rule_id"])
    if existing is None:
        logger.warning("Skipping DELETE %s because rule was not found", scenario["rule_id"])
        return None

    signal = {
        "rule_id": scenario["rule_id"],
        "rule_type": existing["rule_type"],
        "operation": "DELETE",
        "changed_fields": list(existing.keys()),
        "before_state": existing,
        "after_state": None,
        "author": scenario_author(existing),
        "oos_conflicts": [],
    }
    return post_rule_diff(signal)


def simulate_scenario(
    scenario: Dict[str, Any],
    ocs_client: OCSCatalogClient,
    rule_state: RuleStateManager,
) -> Optional[str]:
    operation = scenario["operation"].upper()
    if operation == "INSERT":
        return simulate_insert(scenario, ocs_client)
    if operation == "UPDATE":
        return simulate_update(scenario, ocs_client, rule_state)
    if operation == "DELETE":
        return simulate_delete(scenario, rule_state)
    logger.warning("Skipping unsupported operation %s for %s", operation, scenario.get("rule_id"))
    return None


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    scenarios = read_json(MOCK_DATA_ROOT / "scenarios" / "rule_scenarios.json")["scenarios"]
    read_json(MOCK_DATA_ROOT / "index" / "product_index.json")
    rule_state = RuleStateManager()

    succeeded = 0
    failed = 0
    by_severity: Counter[str] = Counter()
    critical_rule_ids: list[str] = []

    with OCSCatalogClient() as ocs_client:
        for scenario in scenarios:
            severity = simulate_scenario(scenario, ocs_client, rule_state)
            if severity:
                succeeded += 1
                by_severity[severity] += 1
                if severity == "critical":
                    critical_rule_ids.append(scenario["rule_id"])
            else:
                failed += 1

    print(
        json.dumps(
            {
                "total_scenarios": len(scenarios),
                "succeeded": succeeded,
                "failed": failed,
                "by_severity": dict(by_severity),
                "critical_rule_ids": critical_rule_ids,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    run()
