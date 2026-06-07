"""Standalone stale-embedding drift detection and remediation helpers.

This module is intentionally separate from the current pipeline so you can
analyze stale-embedding risk without changing any existing agent code.

The logic follows the guidance in the supplied write-up:
- cosine-similarity checks when both old and refreshed vectors are available
- MRR / rank-drop monitoring when ranking telemetry is present
- query reformulation spikes from query logs
- TTL-based freshness checks from embedding and catalog timestamps
- remediation suggestions for incremental re-embedding, shadow indexing,
  hybrid lexical fallback, and model version pinning
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SIMILARITY_THRESHOLD = 0.85
DEFAULT_MRR_THRESHOLD = 0.75
DEFAULT_REFORMULATION_SPIKE_THRESHOLD = 0.35
DEFAULT_TTL_DAYS = 14

DOMAIN_TTL_DAYS = {
    "news": 30,
    "legal": 180,
    "support": 90,
    "catalog": 14,
    "product": 14,
}

STOPWORDS = {
    "and",
    "for",
    "from",
    "into",
    "more",
    "of",
    "or",
    "the",
    "this",
    "that",
    "with",
}


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _coerce_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", " ")


def _tokenize(value: Any) -> list[str]:
    text = _normalize_text(value)
    if not text:
        return []
    tokens = re.findall(r"[a-z0-9]+", text)
    return [token for token in tokens if len(token) >= 3 and token not in STOPWORDS]


def _text_vector(value: Any) -> Counter[str]:
    return Counter(_tokenize(value))


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    """Compute cosine similarity between two numeric vectors."""

    left_values = [float(item) for item in left]
    right_values = [float(item) for item in right]
    if not left_values or not right_values or len(left_values) != len(right_values):
        return 0.0

    numerator = sum(a * b for a, b in zip(left_values, right_values))
    left_norm = math.sqrt(sum(a * a for a in left_values))
    right_norm = math.sqrt(sum(b * b for b in right_values))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def lexical_similarity(first: Any, second: Any) -> float:
    """Bag-of-words cosine similarity for plain-text reformulation checks."""

    left = _text_vector(first)
    right = _text_vector(second)
    if not left or not right:
        return 0.0

    vocab = set(left) | set(right)
    left_vec = [float(left.get(term, 0)) for term in vocab]
    right_vec = [float(right.get(term, 0)) for term in vocab]
    return cosine_similarity(left_vec, right_vec)


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)

    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _age_in_days(older: Any, newer: datetime | None = None) -> float | None:
    parsed = _parse_datetime(older)
    if parsed is None:
        return None
    anchor = newer or datetime.now(timezone.utc)
    delta = anchor - parsed
    return delta.total_seconds() / 86400.0


def _extract_products(payload: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = payload.get("catalog")
    if isinstance(catalog, dict):
        products = catalog.get("products", [])
    elif isinstance(catalog, list):
        products = catalog
    else:
        products = payload.get("products", [])

    return [product for product in _coerce_list(products) if isinstance(product, dict)]


def _extract_query_logs(payload: dict[str, Any]) -> list[dict[str, Any]]:
    query_logs = payload.get("queryLogs")
    if isinstance(query_logs, list):
        return [log for log in query_logs if isinstance(log, dict)]
    if isinstance(payload.get("telemetry"), dict) and isinstance(payload["telemetry"].get("queryLogs"), list):
        return [log for log in payload["telemetry"].get("queryLogs", []) if isinstance(log, dict)]
    return []


def _product_vector_fields(product: dict[str, Any]) -> tuple[list[float], list[float]] | None:
    old_candidates = (
        product.get("embedding"),
        product.get("cachedEmbedding"),
        product.get("storedEmbedding"),
        product.get("vector"),
    )
    new_candidates = (
        product.get("freshEmbedding"),
        product.get("currentEmbedding"),
        product.get("updatedEmbedding"),
        product.get("recomputedEmbedding"),
        product.get("latestEmbedding"),
    )

    def _coerce_vector(candidate: Any) -> list[float]:
        if not isinstance(candidate, list):
            return []
        values: list[float] = []
        for item in candidate:
            if isinstance(item, (int, float)):
                values.append(float(item))
        return values

    old_vector = next((vector for vector in (_coerce_vector(item) for item in old_candidates) if vector), [])
    new_vector = next((vector for vector in (_coerce_vector(item) for item in new_candidates) if vector), [])
    if old_vector and new_vector and len(old_vector) == len(new_vector):
        return old_vector, new_vector
    return None


def _extract_product_id(product: dict[str, Any], fallback_index: int) -> str:
    for key in ("id", "productId", "product_id", "sku"):
        value = product.get(key)
        if value:
            return str(value)
    return f"product-{fallback_index}"


def _resolve_ttl_days(payload: dict[str, Any]) -> int:
    thresholds = _as_dict(payload.get("thresholds"))
    if isinstance(thresholds.get("staleEmbeddingDays"), (int, float)):
        return int(thresholds["staleEmbeddingDays"])

    for key in ("domain", "dataDomain", "contentType", "documentType"):
        domain = str(payload.get(key) or "").strip().lower()
        if domain and domain in DOMAIN_TTL_DAYS:
            return DOMAIN_TTL_DAYS[domain]
    return DEFAULT_TTL_DAYS


def _resolve_similarity_threshold(payload: dict[str, Any]) -> float:
    thresholds = _as_dict(payload.get("thresholds"))
    value = thresholds.get("embeddingSimilarityThreshold")
    if isinstance(value, (int, float)):
        return float(value)
    return DEFAULT_SIMILARITY_THRESHOLD


def _resolve_reformulation_threshold(payload: dict[str, Any]) -> float:
    thresholds = _as_dict(payload.get("thresholds"))
    value = thresholds.get("queryReformulationSpike")
    if isinstance(value, (int, float)):
        return float(value)
    return DEFAULT_REFORMULATION_SPIKE_THRESHOLD


def _resolve_mrr_threshold(payload: dict[str, Any]) -> float:
    thresholds = _as_dict(payload.get("thresholds"))
    value = thresholds.get("mrrDropThreshold")
    if isinstance(value, (int, float)):
        return float(value)
    return DEFAULT_MRR_THRESHOLD


def analyze_product_staleness(
    product: dict[str, Any],
    *,
    now: datetime | None = None,
    ttl_days: int = DEFAULT_TTL_DAYS,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> dict[str, Any]:
    """Inspect one product or document for stale embedding evidence."""

    reference_time = now or datetime.now(timezone.utc)
    product_id = _extract_product_id(product, 0)
    reasons: list[str] = []
    signals: list[str] = []
    confidence = 0.0
    stale = False

    embedding_updated_at = _parse_datetime(product.get("embeddingUpdatedAt"))
    catalog_updated_at = _parse_datetime(product.get("catalogUpdatedAt") or product.get("updatedAt"))
    vector_pair = _product_vector_fields(product)

    if embedding_updated_at is not None:
        age_days = _age_in_days(embedding_updated_at, reference_time)
        if age_days is not None:
            signals.append(f"embedding_age_days={round(age_days, 2)}")
            if age_days >= ttl_days:
                stale = True
                confidence += 0.35
                reasons.append(
                    f"Embedding age ({age_days:.1f} days) exceeds the freshness TTL of {ttl_days} days."
                )

    if embedding_updated_at is not None and catalog_updated_at is not None and embedding_updated_at < catalog_updated_at:
        stale = True
        confidence += 0.35
        reasons.append("Catalog content was updated after the embedding timestamp.")
        signals.append("catalog_updated_after_embedding")

    if vector_pair is not None:
        old_vector, new_vector = vector_pair
        similarity = cosine_similarity(old_vector, new_vector)
        signals.append(f"vector_similarity={round(similarity, 4)}")
        if similarity < similarity_threshold:
            stale = True
            confidence += 0.45
            reasons.append(
                f"Embedding cosine similarity ({similarity:.3f}) is below the drift threshold of {similarity_threshold:.2f}."
            )

    model_version = str(product.get("embeddingModelVersion") or product.get("embeddingModel") or "").strip()
    expected_version = str(
        product.get("targetEmbeddingModelVersion")
        or product.get("expectedEmbeddingModelVersion")
        or product.get("currentEmbeddingModelVersion")
        or ""
    ).strip()
    if model_version and expected_version and model_version != expected_version:
        stale = True
        confidence += 0.15
        reasons.append(f"Embedding model version changed from {model_version} to {expected_version}.")
        signals.append("model_version_mismatch")

    confidence = round(min(0.99, max(confidence, 0.0)), 2)
    if stale and confidence == 0.0:
        confidence = 0.55

    return {
        "productId": product_id,
        "stale": stale,
        "confidence": confidence,
        "reasons": reasons,
        "signals": signals,
        "embeddingUpdatedAt": product.get("embeddingUpdatedAt"),
        "catalogUpdatedAt": product.get("catalogUpdatedAt") or product.get("updatedAt"),
    }


def analyze_query_reformulations(
    query_logs: list[dict[str, Any]],
    *,
    spike_threshold: float = DEFAULT_REFORMULATION_SPIKE_THRESHOLD,
) -> dict[str, Any]:
    """Detect repeated reformulations within a session or user trail."""

    sessions: dict[str, list[str]] = defaultdict(list)
    raw_rows = 0
    for index, log in enumerate(query_logs):
        raw_rows += 1
        session_id = (
            log.get("sessionId")
            or log.get("session_id")
            or log.get("visitorId")
            or log.get("userId")
            or log.get("traceId")
            or f"row-{index}"
        )
        query = str(log.get("query") or log.get("queryText") or log.get("searchText") or log.get("term") or "").strip()
        if query:
            sessions[str(session_id)].append(query)

    reformulation_sessions = 0
    examples: list[dict[str, Any]] = []
    for session_id, queries in sessions.items():
        if len(queries) < 2:
            continue

        normalized_queries = [_normalize_text(query) for query in queries]
        unique_queries = list(dict.fromkeys(normalized_queries))
        pairwise_scores: list[float] = []
        for left, right in zip(unique_queries, unique_queries[1:]):
            pairwise_scores.append(lexical_similarity(left, right))

        average_similarity = sum(pairwise_scores) / len(pairwise_scores) if pairwise_scores else 0.0
        reformulation = len(unique_queries) > 1 and average_similarity < 0.65
        if reformulation:
            reformulation_sessions += 1
            examples.append(
                {
                    "sessionId": session_id,
                    "queries": unique_queries[:4],
                    "averageSimilarity": round(average_similarity, 4),
                }
            )

    total_sessions = len(sessions)
    reformulation_rate = (reformulation_sessions / total_sessions) if total_sessions else 0.0
    spike = reformulation_rate >= spike_threshold

    return {
        "checkedSessions": total_sessions,
        "reformulationSessions": reformulation_sessions,
        "reformulationRate": round(reformulation_rate, 4),
        "spikeThreshold": spike_threshold,
        "spikeDetected": spike,
        "examples": examples[:5],
    }


def analyze_mrr(metrics: dict[str, Any], *, threshold: float = DEFAULT_MRR_THRESHOLD) -> dict[str, Any]:
    """Track MRR / reciprocal-rank degradation if the payload exposes it."""

    current = metrics.get("mrr")
    if current is None:
        current = metrics.get("meanReciprocalRank")
    if current is None:
        current = metrics.get("reciprocalRank")

    baseline = metrics.get("baselineMrr")
    if baseline is None:
        baseline = metrics.get("baseline_mrr")
    if baseline is None:
        baseline = metrics.get("expectedMrr")

    current_value = float(current) if isinstance(current, (int, float)) else None
    baseline_value = float(baseline) if isinstance(baseline, (int, float)) else None

    if current_value is None and baseline_value is None:
        return {
            "available": False,
            "dropDetected": False,
            "currentMrr": None,
            "baselineMrr": None,
            "drop": None,
            "threshold": threshold,
        }

    drop = None
    if current_value is not None and baseline_value is not None:
        drop = baseline_value - current_value
    elif current_value is not None:
        drop = threshold - current_value

    drop_detected = False
    if current_value is not None and baseline_value is not None:
        drop_detected = current_value < baseline_value and (baseline_value - current_value) >= 0.15
    elif current_value is not None:
        drop_detected = current_value < threshold

    return {
        "available": True,
        "dropDetected": drop_detected,
        "currentMrr": current_value,
        "baselineMrr": baseline_value,
        "drop": drop,
        "threshold": threshold,
    }


def build_stale_embedding_report(
    payload: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a deterministic stale-embedding drift report from JSON payload data."""

    reference_time = now or datetime.now(timezone.utc)
    ttl_days = _resolve_ttl_days(payload)
    similarity_threshold = _resolve_similarity_threshold(payload)
    reformulation_threshold = _resolve_reformulation_threshold(payload)
    mrr_threshold = _resolve_mrr_threshold(payload)

    products = _extract_products(payload)
    query_logs = _extract_query_logs(payload)
    metrics = _as_dict(payload.get("metrics") or payload.get("telemetry"))

    product_findings = [
        analyze_product_staleness(
            product,
            now=reference_time,
            ttl_days=ttl_days,
            similarity_threshold=similarity_threshold,
        )
        for product in products
    ]
    stale_products = [finding for finding in product_findings if finding["stale"]]
    stale_product_ids = [finding["productId"] for finding in stale_products]

    reformulation = analyze_query_reformulations(query_logs, spike_threshold=reformulation_threshold)
    mrr = analyze_mrr(metrics, threshold=mrr_threshold)

    signals = {
        "productFindings": product_findings,
        "staleProducts": stale_products,
        "reformulation": reformulation,
        "mrr": mrr,
    }

    score = 0.0
    reasons: list[str] = []
    if stale_products:
        score += min(0.6, 0.2 + 0.1 * len(stale_products))
        reasons.append("At least one product or document is older than the freshness TTL or changed after the embedding snapshot.")
    if any("vector_similarity" in " ".join(finding["signals"]) for finding in stale_products):
        score += 0.25
        reasons.append("One or more vector comparisons fell below the similarity threshold.")
    if reformulation["spikeDetected"]:
        score += 0.2
        reasons.append("Query reformulation rate is elevated, which is a common retrieval-drift signal.")
    if mrr["dropDetected"]:
        score += 0.25
        reasons.append("MRR / reciprocal-rank quality is below the expected level.")

    if score >= 0.65:
        verdict = "stale_embedding_likely"
        confidence = round(min(0.99, 0.7 + score * 0.3), 2)
    elif score >= 0.35:
        verdict = "stale_embedding_possible"
        confidence = round(min(0.85, 0.45 + score * 0.35), 2)
    else:
        verdict = "not_stale"
        confidence = round(max(0.25, 0.35 + score * 0.2), 2)

    if stale_product_ids and verdict == "not_stale":
        verdict = "stale_embedding_possible"

    recommended_actions = [
        "Refresh embeddings incrementally for the affected documents instead of re-indexing the full corpus.",
        "Prioritize high-traffic or frequently retrieved documents in the re-embedding queue.",
        "Write the refreshed embeddings to a shadow index first and compare retrieval quality before promotion.",
        "Keep a lexical fallback such as BM25 or full-text search for time-sensitive, exact-match terms.",
        "Pin the embedding model version in the index metadata so future upgrades do not mix old and new vectors.",
    ]

    if verdict == "not_stale":
        recommended_actions = [
            "Keep monitoring embedding freshness, MRR, and query reformulation rate.",
            "If the catalog changes, verify that embedding timestamps move forward with the content update.",
            "Use a shadow index before any embedding-model upgrade.",
        ]

    return {
        "verdict": verdict,
        "confidence": confidence,
        "thresholds": {
            "ttlDays": ttl_days,
            "similarityThreshold": similarity_threshold,
            "reformulationSpikeThreshold": reformulation_threshold,
            "mrrThreshold": mrr_threshold,
        },
        "affectedProductIds": stale_product_ids,
        "evidence": signals,
        "reasons": reasons,
        "recommendedFixes": recommended_actions,
        "remediationStrategy": {
            "incrementalReembedding": bool(stale_product_ids),
            "shadowIndex": True,
            "hybridLexicalFallback": True,
            "modelVersionPinning": True,
            "priorityQueue": True,
        },
    }


def solve_stale_embedding_error(payload: dict[str, Any]) -> dict[str, Any]:
    """Convenience wrapper that returns both detection and remediation guidance."""

    report = build_stale_embedding_report(payload)
    return {
        "issue": "stale_embedding",
        "analysis": report,
        "solution": {
            "nextSteps": report["recommendedFixes"],
            "affectedProductIds": report["affectedProductIds"],
            "confidence": report["confidence"],
            "verdict": report["verdict"],
        },
    }


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect stale embeddings and suggest remediation steps.")
    parser.add_argument("--input", required=True, help="Path to a JSON payload to analyze.")
    parser.add_argument("--out", help="Optional path to write the report JSON.")
    parser.add_argument("--now", help="Optional ISO timestamp to use as the current time.")
    args = parser.parse_args()

    payload = _load_json(args.input)
    now = _parse_datetime(args.now) if args.now else None
    report = build_stale_embedding_report(payload, now=now)

    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"saved: {out_path}")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()

