"""
ranking_metrics.py — NDCG@k and MRR computation for OCS Search evaluation.

Implementation
--------------
Uses ``ranx`` when available and compatible with the current Python/numba
environment.  Falls back to a self-contained numpy-free implementation when
ranx's JIT compilation fails (e.g. Python 3.13 + numba incompatibility).

Qrel relevance scale (standard IR practice):
    0 → not relevant
    1 → somewhat relevant
    2 → relevant
    3 → highly relevant
"""

import math
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Pure-Python fallback (no ranx / numba required)
# ---------------------------------------------------------------------------

def _dcg(results: List[str], qrels: Dict[str, int], k: int) -> float:
    """Discounted Cumulative Gain at cutoff k."""
    dcg = 0.0
    for rank, pid in enumerate(results[:k], start=1):
        rel = qrels.get(pid, 0)
        if rel > 0:
            dcg += rel / math.log2(rank + 1)
    return dcg


def _ideal_dcg(qrels: Dict[str, int], k: int) -> float:
    """Ideal DCG: sort relevance scores descending and compute DCG@k."""
    sorted_rels = sorted(qrels.values(), reverse=True)
    idcg = 0.0
    for rank, rel in enumerate(sorted_rels[:k], start=1):
        if rel > 0:
            idcg += rel / math.log2(rank + 1)
    return idcg


def _ndcg_at_k(results: List[str], qrels: Dict[str, int], k: int) -> float:
    idcg = _ideal_dcg(qrels, k)
    if idcg == 0:
        return 0.0
    return _dcg(results, qrels, k) / idcg


def _mrr(results: List[str], qrels: Dict[str, int]) -> float:
    """Mean Reciprocal Rank (first relevant document)."""
    for rank, pid in enumerate(results, start=1):
        if qrels.get(pid, 0) > 0:
            return 1.0 / rank
    return 0.0


def _compute_pure(
    results: List[str],
    qrels: Dict[str, int],
    k: int,
) -> dict:
    """Pure-Python NDCG@k and MRR — no external dependencies."""
    return {
        f"ndcg@{k}": round(_ndcg_at_k(results, qrels, k), 4),
        "mrr":        round(_mrr(results, qrels), 4),
    }


# ---------------------------------------------------------------------------
# ranx wrapper (preferred when JIT compiles successfully)
# ---------------------------------------------------------------------------

def _compute_ranx(
    query: str,
    results: List[str],
    qrels: Dict[str, int],
    k: int,
) -> Optional[dict]:
    """
    Try computing via ranx.  Returns None on any import/JIT error so the
    caller can fall back to the pure-Python implementation.
    """
    try:
        from ranx import Qrels, Run, evaluate  # type: ignore

        n = len(results)
        run_dict  = {query: {pid: float(n - rank) for rank, pid in enumerate(results)}}
        qrels_obj = Qrels({query: {pid: int(rel) for pid, rel in qrels.items()}})
        run_obj   = Run(run_dict)
        raw = evaluate(run_obj, qrels_obj, [f"ndcg@{k}", "mrr"])
        return {
            f"ndcg@{k}": round(float(raw[f"ndcg@{k}"]), 4),
            "mrr":        round(float(raw["mrr"]), 4),
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_ranking_metrics(
    query: str,
    results: List[str],
    qrels: Dict[str, int],
    k: int = 10,
) -> dict:
    """
    Compute NDCG@k and MRR for a single system's ranked results.

    Tries ranx first; falls back to a pure-Python implementation if ranx's
    numba JIT fails (e.g. Python 3.13 incompatibility).

    Parameters
    ----------
    query:
        Search query string, used as the query ID for ranx.
    results:
        Ordered list of product IDs returned by the system.
    qrels:
        Ground-truth relevance judgments: ``{product_id: relevance_score}``.
    k:
        Cutoff for NDCG (default 10).
    """
    if not results or not qrels:
        return {f"ndcg@{k}": 0.0, "mrr": 0.0}

    # Try ranx first (more battle-tested, handles edge cases well)
    ranx_result = _compute_ranx(query, results, qrels, k)
    if ranx_result is not None:
        return ranx_result

    # Fallback: pure-Python implementation
    return _compute_pure(results, qrels, k)


def compare_systems(
    query: str,
    baseline_results: List[str],
    candidate_results: List[str],
    qrels: Dict[str, int],
    k: int = 10,
) -> dict:
    """
    Compare baseline and candidate systems using NDCG@k and MRR.

    Returns a report dict with:
    - ``baseline``:          metrics for baseline-a
    - ``candidate``:         metrics for the candidate system
    - ``ndcg@{k}_delta``:   candidate − baseline NDCG (positive = improvement)
    - ``mrr_delta``:         candidate − baseline MRR
    - ``improved``:          True if candidate NDCG@k strictly exceeds baseline
    - ``regression``:        True if candidate NDCG@k is more than 0.02 below baseline
    """
    ndcg_key = f"ndcg@{k}"

    baseline_m  = compute_ranking_metrics(query, baseline_results,  qrels, k)
    candidate_m = compute_ranking_metrics(query, candidate_results, qrels, k)

    b_ndcg = baseline_m.get(ndcg_key)
    c_ndcg = candidate_m.get(ndcg_key)
    b_mrr  = baseline_m.get("mrr")
    c_mrr  = candidate_m.get("mrr")

    ndcg_delta = round(c_ndcg - b_ndcg, 4) if (c_ndcg is not None and b_ndcg is not None) else None
    mrr_delta  = round(c_mrr  - b_mrr,  4) if (c_mrr  is not None and b_mrr  is not None) else None

    return {
        "baseline":            baseline_m,
        "candidate":           candidate_m,
        f"{ndcg_key}_delta":  ndcg_delta,
        "mrr_delta":           mrr_delta,
        "improved":            (ndcg_delta or 0) > 0,
        "regression":          (ndcg_delta or 0) < -0.02,
    }
