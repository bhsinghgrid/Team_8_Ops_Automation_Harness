"""Capability mapping helpers for signal triage."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


CAPABILITY_BY_SIGNAL = {
    "empty_query": "browse_intent",
    "catalog_delta": "catalog_completeness",
    "catalog_index_gap": "catalog",
    "catalog_freshness_breach": "catalog",
    "failed_query": "search_relevance",
    "low_ctr": "search_performance",
    "low_result_count": "search_relevance",
    "stale_suggestion": "autocomplete_freshness",
    "autocomplete_miss": "autocomplete_coverage",
    "autocomplete_fail": "autocomplete",
    "autocomplete_zero_suggestions": "autocomplete",
    "autocomplete_latency_spike": "autocomplete",
    "autocomplete_relevance_regression": "autocomplete",
    "merchandising_rule_conflict": "merchandising_governance",
    "zero_result_cluster": "semantic_search",
    "missing_products_cluster": "catalog",
    "missing_facets": "search_api",
    "semantic_index_gap": "semantic_index",
    "semantic_index_stale": "semantic_index",
    "stale_embedding": "semantic_index",
    "semantic_recall_drop": "semantic_index",
    "vector_search_latency_spike": "semantic_index",
    "personalization_fallback_spike": "personalization",
    "feature_service_degraded": "personalization",
    "personalization_uplift_drop": "personalization",
    "rule_diff": "merchandising_controls",
    "rule_conflict": "merchandising_controls",
    "policy_violation": "merchandising_controls",
    "pinning_failure": "merchandising_controls",
    "exclusion_policy_violation": "merchandising_controls",
    "merch_rule_conflict": "merchandising_controls",
    "campaign_result_miss": "merchandising_controls",
    "latency_spike": "search_api",
}

_CAPABILITY_ALIASES = {
    "browse_intent": "browse_intent",
    "search_experience": "browse_intent",
    "search_relevance": "search_relevance",
    "search_performance": "search_performance",
    "semantic_search": "semantic_search",
    "semantic_retrieval": "semantic_search",
    "semantic_index": "semantic_index",
    "catalog": "catalog",
    "catalog_completeness": "catalog_completeness",
    "autocomplete": "autocomplete",
    "autocomplete_coverage": "autocomplete_coverage",
    "autocomplete_freshness": "autocomplete_freshness",
    "personalization": "personalization",
    "merchandising_controls": "merchandising_controls",
    "merchandising_governance": "merchandising_governance",
    "search_api": "search_api",
}

_BROWSE_INTENT_SIGNAL_TYPES = frozenset({"empty_query", "low_result_count", "missing_facets"})


def _normalize_label(value: Any) -> str:
    label = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    while "__" in label:
        label = label.replace("__", "_")
    return label.strip("_")


def _normalize_capability(value: Any) -> str:
    label = _normalize_label(value)
    if not label:
        return ""
    if label == "unknown":
        return ""
    return _CAPABILITY_ALIASES.get(label, label)


def _coerce_signal(signal: Any) -> dict[str, Any]:
    if isinstance(signal, Mapping):
        return dict(signal)
    if isinstance(signal, str):
        return {"type": signal}
    return {"type": str(signal)}


def _extract_query(signal: Mapping[str, Any]) -> Any:
    for key in ("query", "query_text", "queryText"):
        if key in signal:
            return signal.get(key)

    entities = signal.get("entities")
    if isinstance(entities, Mapping):
        for key in ("query", "query_text", "queryText"):
            if key in entities:
                return entities.get(key)

    payload = signal.get("payload")
    if isinstance(payload, Mapping):
        for key in ("query", "query_text", "queryText"):
            if key in payload:
                return payload.get(key)

    return None


def _is_blank_query(signal: Mapping[str, Any]) -> bool:
    query = _extract_query(signal)
    return isinstance(query, str) and not query.strip()


def _append_text(chunks: list[str], value: Any) -> None:
    if value is None:
        return
    if isinstance(value, Mapping):
        for key in sorted(value):
            nested = value.get(key)
            if nested is None:
                continue
            if isinstance(nested, (Mapping, Sequence)) and not isinstance(nested, (str, bytes, bytearray)):
                _append_text(chunks, nested)
            else:
                text = str(nested).strip()
                if text:
                    chunks.append(f"{key}={text}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _append_text(chunks, item)
        return

    text = str(value).strip()
    if text:
        chunks.append(text)


def _signal_blob(signal: Mapping[str, Any]) -> str:
    chunks: list[str] = []
    for key in (
        "type",
        "source",
        "summary",
        "message",
        "reason",
        "description",
        "recommendedAction",
        "capability",
        "source_capability",
        "target_capability",
        "family",
        "capability_family",
    ):
        _append_text(chunks, signal.get(key))

    query = _extract_query(signal)
    if query is not None:
        _append_text(chunks, query)

    for key in ("entities", "metrics", "evidence"):
        _append_text(chunks, signal.get(key))

    payload = signal.get("payload")
    if isinstance(payload, Mapping):
        _append_text(chunks, payload)

    return " ".join(chunk.lower() for chunk in chunks if str(chunk).strip())


def _infer_from_text(blob: str) -> str:
    if not blob:
        return "unknown"

    if any(term in blob for term in ("empty query", "blank query", "browse intent", "browse or trending intent", "trending intent")):
        return "browse_intent"

    if any(term in blob for term in ("stale suggestion", "stale suggestions", "freshness", "stale autocomplete")):
        return "autocomplete_freshness"
    if any(term in blob for term in ("autocomplete", "typeahead", "suggestion", "missed prefix", "prefix coverage")):
        return "autocomplete_coverage"

    if any(term in blob for term in ("merchandising rule", "merchandising", "rule diff", "rule conflict", "policy violation", "pinning failure", "pinning", "exclusion", "campaign")):
        return "merchandising_governance" if any(term in blob for term in ("governance", "campaign", "pinning", "exclusion")) else "merchandising_controls"

    if any(term in blob for term in ("catalog item", "missing products", "missing attribute", "missing attributes", "attribute gap", "catalog completeness", "out of stock", "inventory")):
        return "catalog_completeness"
    if "catalog" in blob:
        return "catalog"

    if any(term in blob for term in ("stale embedding", "semantic index", "vector", "embedding", "index gap", "semantic recall", "semantic_index")):
        return "semantic_index"

    if any(term in blob for term in ("zero result cluster", "zero results", "no results", "no matches", "semantic miss", "query reformulation")):
        return "semantic_search"

    if any(term in blob for term in ("missing facets", "facet configuration", "filterable fields", "no facet data", "facet data", "facets")):
        return "search_api"

    if any(term in blob for term in ("low result count", "fewer products", "below threshold", "recall", "synonym coverage", "searchable attributes", "match count", "result count")):
        return "search_relevance"

    if any(term in blob for term in ("personalization", "feature service", "uplift", "fallback")):
        return "personalization"

    if any(term in blob for term in ("latency", "timeout", "5xx", "error")):
        return "search_api"

    return "unknown"


def infer_capability_from_signal(signal: Any) -> str:
    payload = _coerce_signal(signal)

    for key in ("capability", "source_capability", "target_capability", "family", "capability_family"):
        capability = _normalize_capability(payload.get(key))
        if capability:
            return capability

    signal_type = _normalize_label(payload.get("type"))
    blob = _signal_blob(payload)

    if _is_blank_query(payload) and (
        signal_type in _BROWSE_INTENT_SIGNAL_TYPES
        or any(term in blob for term in ("browse intent", "browse or trending intent", "trending intent"))
    ):
        return "browse_intent"

    if signal_type in CAPABILITY_BY_SIGNAL:
        return CAPABILITY_BY_SIGNAL[signal_type]

    return _infer_from_text(blob)


def capability_family(signal_type: str, capability: str) -> str:
    if capability in {"browse_intent", "search_relevance", "search_performance", "search_api"} or signal_type in {
        "empty_query",
        "low_result_count",
        "low_ctr",
        "missing_facets",
    }:
        return "search_experience"
    if capability in {"semantic_search", "ranking"} or signal_type in {"zero_result_cluster", "query_reformulation"}:
        return "semantic_retrieval"
    if capability in {"catalog", "catalog_completeness"} or signal_type in {"catalog_delta", "catalog_index_gap", "catalog_freshness_breach", "missing_products_cluster"}:
        return "catalog"
    if capability in {"autocomplete", "autocomplete_coverage", "autocomplete_freshness"} or signal_type in {"autocomplete_fail", "autocomplete_zero_suggestions", "autocomplete_latency_spike", "autocomplete_relevance_regression"}:
        return "autocomplete"
    if capability == "semantic_index" or signal_type in {"semantic_index_gap", "semantic_index_stale", "semantic_recall_drop", "vector_search_latency_spike"}:
        return "semantic_retrieval"
    if capability == "personalization" or signal_type in {"personalization_fallback_spike", "feature_service_degraded", "personalization_uplift_drop"}:
        return "personalization"
    if capability in {"merchandising_controls", "merchandising_governance", "rule_engine"} or signal_type in {"rule_diff", "rule_conflict", "policy_violation", "pinning_failure", "exclusion_policy_violation", "merch_rule_conflict", "campaign_result_miss"}:
        return "merchandising_controls"
    return capability or "unknown"
