"""Deterministic remediation-plan generator used by the FixPlanAgent."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tools.data_gap_tools import classify_data_gap
from tools.index_analysis_tools import diff_index_settings
from environment.AgentsRLM.stale_embedding.constants import (
    EVIDENCE_CONFIRMED,
    EVIDENCE_PROBABLE,
    STATUS_STALE,
)
from environment.AgentsRLM.stale_embedding.remediation import build_stale_embedding_report
from tools.synonym_tools import propose_synonym_mappings


def _normalize_catalog(catalog: Any) -> dict[str, Any]:
    if isinstance(catalog, dict):
        payload = dict(catalog)
        payload.setdefault("products", [])
        return payload
    if isinstance(catalog, list):
        return {"products": catalog}
    return {"products": []}


def _flatten_signals(signals: Any) -> list[dict[str, Any]]:
    if isinstance(signals, list):
        return [signal for signal in signals if isinstance(signal, dict)]
    if not isinstance(signals, dict):
        return []

    flattened: list[dict[str, Any]] = []
    direct_signals = signals.get("signals")
    if isinstance(direct_signals, list):
        flattened.extend(signal for signal in direct_signals if isinstance(signal, dict))

    signals_by_type = signals.get("signalsByType")
    if isinstance(signals_by_type, dict):
        for items in signals_by_type.values():
            if isinstance(items, list):
                flattened.extend(signal for signal in items if isinstance(signal, dict))

    return flattened


def _signal_types(signals: Any) -> set[str]:
    return {
        str(signal.get("type"))
        for signal in _flatten_signals(signals)
        if isinstance(signal.get("type"), str) and signal.get("type")
    }


def _coerce_string_list(values: Any) -> list[str]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for item in values:
        if isinstance(item, str):
            normalized = item.strip()
            if normalized:
                result.append(normalized)
    return result


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _incident_query(query: Any, signals: Any) -> str:
    if isinstance(query, str) and query.strip():
        return query.strip()
    if isinstance(signals, dict):
        candidate = signals.get("query")
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    for signal in _flatten_signals(signals):
        entities = signal.get("entities", {}) if isinstance(signal.get("entities"), dict) else {}
        for key in ("query", "phrase", "term"):
            value = entities.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.strip():
                        return item.strip()

    if isinstance(signals, dict):
        query_logs = signals.get("queryLogs")
        if isinstance(query_logs, list):
            for log in query_logs:
                if not isinstance(log, dict):
                    continue
                value = log.get("query")
                if isinstance(value, str) and value.strip():
                    return value.strip()

    return ""


def _shadow_gap_profile(signals: Any, incident_query: str) -> dict[str, Any]:
    default = {
        "gapType": "unknown",
        "reason": "No shadow-test comparison was available, so the plan is driven by the observed signals instead.",
        "confidence": "medium",
        "settingDiff": {},
    }
    if not isinstance(signals, dict):
        return default

    shadow = signals.get("shadowTest")
    if not isinstance(shadow, dict):
        return default

    baseline = shadow.get("primary") or shadow.get("baseline")
    candidate = shadow.get("candidate")
    if not isinstance(baseline, dict) or not isinstance(candidate, dict):
        return default

    baseline_settings = baseline.get("settings", {}) if isinstance(baseline.get("settings"), dict) else {}
    candidate_settings = candidate.get("settings", {}) if isinstance(candidate.get("settings"), dict) else {}
    setting_diff = diff_index_settings(baseline_settings, candidate_settings)
    gap_type, reason, confidence = classify_data_gap(
        incident_query=incident_query,
        baseline_docs=_int_value(baseline.get("docs", baseline.get("documents", 0))),
        candidate_docs=_int_value(candidate.get("docs", candidate.get("documents", 0))),
        baseline_results=_int_value(baseline.get("results", baseline.get("results_count", 0))),
        candidate_results=_int_value(candidate.get("results", candidate.get("results_count", 0))),
        shadow_status=str(candidate.get("status", "unknown")),
        setting_diff=setting_diff,
    )
    return {
        "gapType": gap_type,
        "reason": reason,
        "confidence": confidence,
        "settingDiff": setting_diff,
    }


def _shadow_baseline_results(signals: Any) -> int:
    if not isinstance(signals, dict):
        return 0

    shadow = signals.get("shadowTest")
    if not isinstance(shadow, dict):
        return 0

    baseline = shadow.get("primary") or shadow.get("baseline")
    if not isinstance(baseline, dict):
        return 0

    return _int_value(baseline.get("results", baseline.get("results_count", 0)))


def _catalog_field_candidates(catalog: Any) -> set[str]:
    payload = _normalize_catalog(catalog)
    candidates: set[str] = set()
    excluded = {
        "id",
        "price",
        "stock",
        "catalogUpdatedAt",
        "embeddingUpdatedAt",
        "createdAt",
        "updatedAt",
    }

    for product in payload.get("products", []):
        if not isinstance(product, dict):
            continue
        for key, value in product.items():
            if key in excluded:
                continue
            if isinstance(value, str) and value.strip():
                candidates.add(key)
                continue
            if isinstance(value, list) and any(isinstance(item, str) and item.strip() for item in value):
                candidates.add(key)
                continue
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if isinstance(subkey, str) and isinstance(subvalue, str) and subvalue.strip():
                        candidates.add(subkey)

    return candidates


def _required_attribute_candidates(signals: Any) -> set[str]:
    candidates: set[str] = set()
    if not isinstance(signals, dict):
        return candidates

    candidates.update(_coerce_string_list(signals.get("requiredAttributes")))

    for signal in _flatten_signals(signals):
        entities = signal.get("entities", {}) if isinstance(signal.get("entities"), dict) else {}
        for key in ("attributes", "fields"):
            candidates.update(_coerce_string_list(entities.get(key)))

    return candidates


def _current_searchable_fields(signals: Any) -> set[str]:
    if not isinstance(signals, dict):
        return set()

    shadow = signals.get("shadowTest")
    if not isinstance(shadow, dict):
        return set()

    baseline = shadow.get("primary") or shadow.get("baseline")
    if not isinstance(baseline, dict):
        return set()

    settings = baseline.get("settings")
    if not isinstance(settings, dict):
        return set()

    return set(_coerce_string_list(settings.get("searchableAttributes")))


def _field_descriptor(field_name: str) -> dict[str, Any]:
    if field_name == "tags":
        field_type = "array"
        weight = 0.85
    elif field_name == "title":
        field_type = "text"
        weight = 1.0
    elif field_name == "description":
        field_type = "text"
        weight = 0.75
    elif field_name == "category":
        field_type = "text"
        weight = 0.8
    else:
        field_type = "text" if len(field_name) > 6 else "keyword"
        weight = 0.65

    return {
        "name": field_name,
        "type": field_type,
        "searchable": True,
        "weight": weight,
    }


def _stale_embedding_targets(signals: Any) -> list[str]:
    product_ids: set[str] = set()
    for signal in _flatten_signals(signals):
        if signal.get("type") != "stale_embedding":
            continue
        entities = signal.get("entities", {})
        if not isinstance(entities, dict):
            continue
        ids = entities.get("productIds") or entities.get("productId") or []
        if isinstance(ids, str):
            ids = [ids]
        if isinstance(ids, list):
            for product_id in ids:
                if isinstance(product_id, str) and product_id:
                    product_ids.add(product_id)
    return sorted(product_ids)


def _stale_embedding_payload(signals: Any, catalog: Any) -> dict[str, Any]:
    payload = dict(signals) if isinstance(signals, dict) else {}
    payload["catalog"] = _normalize_catalog(catalog)
    return payload


def _merchandising_rule_ids(signals: Any) -> list[str]:
    rule_ids: set[str] = set()
    for signal in _flatten_signals(signals):
        if signal.get("type") != "merchandising_rule_conflict":
            continue
        entities = signal.get("entities", {})
        if not isinstance(entities, dict):
            continue
        ids = entities.get("ruleIds") or entities.get("ruleId") or []
        if isinstance(ids, str):
            ids = [ids]
        if isinstance(ids, list):
            for rule_id in ids:
                if isinstance(rule_id, str) and rule_id:
                    rule_ids.add(rule_id)
    return sorted(rule_ids)


def _build_phases(
    *,
    needs_synonyms: bool,
    needs_embedding_refresh: bool,
    needs_catalog_update: bool,
    needs_merchandising_update: bool,
) -> list[dict[str, Any]]:
    phases: list[dict[str, Any]] = []
    phase_number = 1

    def add_phase(action: str, duration: str, verification: str) -> None:
        nonlocal phase_number
        phases.append(
            {
                "phase": phase_number,
                "duration": duration,
                "action": action,
                "verification": verification,
            }
        )
        phase_number += 1

    if needs_synonyms:
        add_phase("Enable synonyms", "30 min", "Query starts matching broader vocabulary")
    if needs_embedding_refresh:
        add_phase("Refresh stale embeddings", "20 min", "Embedding timestamps align with the catalog")
    if needs_catalog_update:
        add_phase("Add searchable fields", "15 min", "Reindexing exposes the observed catalog fields")
    if needs_merchandising_update:
        add_phase("Update merchandising rules", "30 min", "Relevance ranking no longer boosts the conflicting rules")

    add_phase("Validate and monitor", "1 day", "Metrics improve and regressions stay contained")
    return phases


def _estimate_timeline(remediation_phase_count: int) -> str:
    if remediation_phase_count <= 1:
        return "under 1 hour + monitoring"
    if remediation_phase_count == 2:
        return "1-2 hours + monitoring"
    if remediation_phase_count <= 4:
        return "same-day remediation + monitoring"
    return "multi-hour remediation + monitoring"


def _build_merchandising_patch(signals: Any, signal_types: set[str]) -> dict[str, Any]:
    payload = signals if isinstance(signals, dict) else {}
    thresholds = payload.get("thresholds", {}) if isinstance(payload.get("thresholds"), dict) else {}
    low_stock_threshold = _int_value(thresholds.get("lowStockThreshold", 5)) or 5
    conflict_rule_ids = _merchandising_rule_ids(signals)

    inventory_count = len(payload.get("inventory", [])) if isinstance(payload.get("inventory"), list) else 0
    conversion_count = len(payload.get("conversion", [])) if isinstance(payload.get("conversion"), list) else 0
    merch_conflict_detected = bool(signal_types & {"merchandising_rule_conflict", "rule_conflict", "merch_rule_conflict", "policy_violation", "pinning_failure", "exclusion_policy_violation"})

    rules: list[dict[str, Any]] = [
        {
            "id": "rule-promote-in-stock",
            "name": "Promote in-stock items",
            "condition": f"stock > {low_stock_threshold}",
            "boost": 1.5,
            "priority": "high",
        },
        {
            "id": "rule-boost-relevant",
            "name": "Boost relevant matches",
            "condition": "relevance_score > 0.7",
            "boost": 2.0,
            "priority": "critical",
        },
    ]

    if conflict_rule_ids or merch_conflict_detected:
        rules.append(
            {
                "id": "rule-conflict-guard",
                "name": "Suppress conflicting campaign boosts",
                "condition": "conflicting_merchandising_rule_detected = true",
                "affectedRuleIds": conflict_rule_ids,
                "priority": "critical",
            }
        )

    return {
        "description": "Adjust merchandising rules to protect relevance and in-stock substitutes.",
        "rules": rules,
        "sourceSummary": {
            "inventoryCount": inventory_count,
            "conversionCount": conversion_count,
            "conflictRuleIds": len(conflict_rule_ids),
        },
    }


def build_plan(query, signals, catalog):
    """Build a remediation plan from the incident payload and local evidence."""

    catalog_payload = _normalize_catalog(catalog)
    signal_payload = signals if isinstance(signals, dict) else {}
    incident_query = _incident_query(query, signal_payload)
    signal_types = _signal_types(signal_payload)
    gap_profile = _shadow_gap_profile(signal_payload, incident_query)
    query_logs = signal_payload.get("queryLogs", []) if isinstance(signal_payload.get("queryLogs"), list) else []

    current_searchable_fields = _current_searchable_fields(signal_payload)
    discovered_fields = (_catalog_field_candidates(catalog_payload) | _required_attribute_candidates(signal_payload)) - current_searchable_fields
    searchable_fields = sorted(discovered_fields)
    stale_embedding_report = build_stale_embedding_report(_stale_embedding_payload(signal_payload, catalog_payload))
    stale_embedding_targets = sorted(
        set(_stale_embedding_targets(signal_payload))
        | set(stale_embedding_report.get("affectedProductIds", []))
    )
    stale_embedding_verdict = str(stale_embedding_report.get("verdict") or "")
    stale_embedding_detected = stale_embedding_report.get("status") == STATUS_STALE or stale_embedding_verdict in {
        EVIDENCE_CONFIRMED,
        EVIDENCE_PROBABLE,
    }
    needs_synonyms = bool(
        signal_types
        & {
            "failed_query",
            "autocomplete_miss",
            "stale_suggestion",
        }
    ) or gap_profile["gapType"] in {"query_vocabulary_gap", "rule_configuration_diff"}
    needs_embedding_refresh = bool(stale_embedding_targets) or stale_embedding_detected or gap_profile["gapType"] in {
        "semantic_index_gap",
        "semantic_index_stale",
        "semantic_recall_drop",
    }
    needs_catalog_update = bool(searchable_fields) or gap_profile["gapType"] in {
        "query_vocabulary_gap",
        "candidate_catalog_delta",
        "rule_configuration_diff",
    }
    needs_merchandising_update = bool(
        signal_types
        & {
            "merchandising_rule_conflict",
            "rule_conflict",
            "merch_rule_conflict",
            "policy_violation",
            "pinning_failure",
            "exclusion_policy_violation",
            "campaign_result_miss",
        }
    ) or bool(_merchandising_rule_ids(signal_payload)) or bool(signal_payload.get("inventory")) or bool(signal_payload.get("conversion"))

    embedding_actions = (
        list(stale_embedding_report.get("recommendedFixes", []))
        if stale_embedding_detected
        else [
            "Re-embed affected catalog items after the latest catalog update",
            "Upsert refreshed vectors into the semantic index",
            "Verify embedding timestamps are aligned with catalog timestamps",
        ]
        if needs_embedding_refresh
        else [
            "No stale embeddings were detected; keep monitoring semantic freshness on the next catalog sync",
        ]
    )

    synonym_mappings = propose_synonym_mappings(
        query=incident_query,
        catalog=catalog_payload,
        query_logs=query_logs,
    )

    phases = _build_phases(
        needs_synonyms=needs_synonyms or bool(synonym_mappings),
        needs_embedding_refresh=needs_embedding_refresh,
        needs_catalog_update=needs_catalog_update,
        needs_merchandising_update=needs_merchandising_update,
    )
    remediation_phases = [phase for phase in phases if phase["action"] != "Validate and monitor"]

    catalog_patch = {
        "description": "Align searchable fields with the catalog content that is actually present in this incident.",
        "searchableFields": {
            "current": sorted(current_searchable_fields),
            "add": searchable_fields,
            "rationale": "Expose the observed catalog fields that are not currently searchable.",
        },
        "fields": [_field_descriptor(field_name) for field_name in searchable_fields],
        "catalogSize": len(catalog_payload.get("products", [])) if isinstance(catalog_payload.get("products", []), list) else 0,
    }

    embedding_patch = {
        "description": "Refresh stale embeddings and rebuild the semantic index when the incident points to semantic drift.",
        "refreshEmbeddings": needs_embedding_refresh,
        "rebuildSemanticIndex": needs_embedding_refresh,
        "semanticGapDetected": gap_profile["gapType"] in {"semantic_index_gap", "semantic_index_stale", "semantic_recall_drop"},
        "staleEmbeddingDetected": stale_embedding_detected,
        "staleEmbeddingVerdict": stale_embedding_verdict,
        "staleEmbeddingEvidenceLevel": stale_embedding_report.get("evidenceLevel"),
        "staleEmbeddingStatus": stale_embedding_report.get("status"),
        "staleEmbeddingConfidence": stale_embedding_report.get("confidence"),
        "staleEmbeddingReasons": stale_embedding_report.get("reasons", []),
        "affectedProductIds": stale_embedding_targets,
        "affectedCount": len(stale_embedding_targets),
        "verification": "Affected products are re-embedded and search recall improves",
        "actions": embedding_actions,
    }

    autocomplete_patch = {
        "description": "Generate synonym and query-expansion candidates from catalog and query-log evidence.",
        "enableSynonyms": bool(needs_synonyms or synonym_mappings),
        "synonymMappings": synonym_mappings,
        "sourceSummary": {
            "gapType": gap_profile["gapType"],
            "catalogProducts": len(catalog_payload.get("products", [])) if isinstance(catalog_payload.get("products", []), list) else 0,
            "queryLogs": len(query_logs),
            "proposedTerms": len(synonym_mappings),
        },
    }

    merchandising_patch = _build_merchandising_patch(signal_payload, signal_types)

    plan = {
        "query": incident_query or "",
        "issueProfile": {
            "gapType": gap_profile["gapType"],
            "gapReason": gap_profile["reason"],
            "gapConfidence": gap_profile["confidence"],
            "signalTypes": sorted(signal_types),
            "currentSearchableFields": sorted(current_searchable_fields),
            "proposedSearchableFields": searchable_fields,
            "staleEmbeddingVerdict": stale_embedding_verdict,
            "staleEmbeddingEvidenceLevel": stale_embedding_report.get("evidenceLevel"),
            "staleEmbeddingStatus": stale_embedding_report.get("status"),
            "staleEmbeddingConfidence": stale_embedding_report.get("confidence"),
        },
        "staleEmbedding": {
            "verdict": stale_embedding_verdict,
            "evidenceLevel": stale_embedding_report.get("evidenceLevel"),
            "status": stale_embedding_report.get("status"),
            "confidence": stale_embedding_report.get("confidence"),
            "affectedProductIds": stale_embedding_targets,
            "reasons": stale_embedding_report.get("reasons", []),
        },
        "issuesIdentified": sum(
            1
            for flag in (
                bool(needs_synonyms or synonym_mappings),
                needs_embedding_refresh,
                needs_catalog_update,
                needs_merchandising_update,
            )
            if flag
        ),
        "fixOrder": [phase["action"] for phase in phases],
        "catalogPatch": catalog_patch,
        "embeddingPatch": embedding_patch,
        "autocompletePatch": autocomplete_patch,
        "merchandisingPatch": merchandising_patch,
        "implementation": {
            "timeline": _estimate_timeline(len(remediation_phases)),
            "phases": phases,
        },
        "expectedOutcome": {
            "searchResults": {
                "before": _shadow_baseline_results(signal_payload),
                "after": "positive results",
                "improvement": "coverage restored",
            },
            "metrics": {
                "ctr": "expected lift",
                "latency": "stable after the change",
                "relevance": "improves with broader field and synonym coverage",
                "semanticRecall": "stale -> refreshed" if needs_embedding_refresh else "unchanged",
            },
        },
    }
    return plan


def save_json(path, data):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return str(output_path)
