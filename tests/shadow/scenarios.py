"""
scenarios.py — Predefined test scenarios for shadow evaluation.

Each scenario defines:
  - What each OCS route returns (for the mock HTTP server)
  - Relevance judgments (qrels) for ranx NDCG@k / MRR computation
  - Expected S2N, decision, and whether ranking quality should improve

Qrel relevance scale:
    0 → not relevant
    1 → somewhat relevant
    2 → relevant
    3 → highly relevant

S2N thresholds (from CanaryEvaluationAgent):
    >= 5.0  → PROMOTE
    2.0–4.9 → HOLD
    < 2.0   → ROLLBACK
"""

SCENARIOS = {
    # -----------------------------------------------------------------------
    # PROMOTE: baselines identical (zero noise), candidate adds 5 highly
    # relevant products → candidate_diffs=5, noise_diffs=0 → S2N = 5.0
    #
    # Qrels: sku-004 to sku-008 are the highly/moderately relevant products
    # that only the candidate retrieves. Baseline misses them entirely.
    # → NDCG@10 candidate >> baseline → ranking_metrics.improved = True
    # -----------------------------------------------------------------------
    "promote": {
        "description": (
            "Stable system (no noise), candidate adds 5 highly relevant products. "
            "Expected S2N = 5.0 → PROMOTE.  NDCG should improve significantly."
        ),
        "query": "hybrid work backpack",
        "routes": {
            "baseline-a": ["sku-001", "sku-002", "sku-003"],
            "baseline-b": ["sku-001", "sku-002", "sku-003"],  # identical → noise = 0
            "candidate":  [
                "sku-001", "sku-002", "sku-003",
                "sku-004", "sku-005", "sku-006", "sku-007", "sku-008",
            ],
        },
        # sku-004..008 are the relevant items the fix retrieves;
        # sku-001 is marginally relevant; sku-002/003 are not relevant.
        "qrels": {
            "sku-004": 3,  # highly relevant
            "sku-005": 3,  # highly relevant
            "sku-006": 2,  # relevant
            "sku-007": 2,  # relevant
            "sku-008": 1,  # somewhat relevant
            "sku-001": 1,  # somewhat relevant
            "sku-002": 0,
            "sku-003": 0,
        },
        "expected_s2n": 5.0,
        "expected_decision": "PROMOTE",
        "expected_ndcg_improved": True,   # candidate NDCG > baseline NDCG
    },

    # -----------------------------------------------------------------------
    # HOLD: minor reordering noise (2 position offsets), candidate adds 4 new
    # products → candidate_diffs=4, noise_diffs=2 → S2N = 2.0
    #
    # Qrels: only sku-006 is highly relevant (the fix finds it), others are
    # only moderately improved → moderate NDCG gain.
    # -----------------------------------------------------------------------
    "hold": {
        "description": (
            "System has minor ordering noise. Candidate adds 4 products. "
            "Expected S2N = 2.0 → HOLD.  Moderate NDCG improvement."
        ),
        "query": "ergonomic laptop stand",
        "routes": {
            "baseline-a": ["sku-001", "sku-002", "sku-003", "sku-004", "sku-005"],
            # sku-002/003 swapped → 2 position offsets = noise_diffs = 2
            "baseline-b": ["sku-001", "sku-003", "sku-002", "sku-004", "sku-005"],
            "candidate":  [
                "sku-001", "sku-002", "sku-003", "sku-004", "sku-005",
                "sku-006", "sku-007", "sku-008", "sku-009",
            ],
        },
        # sku-006 is the only truly relevant new item found by the candidate.
        # sku-007/008/009 bring minimal value (rel=1).
        "qrels": {
            "sku-006": 3,  # highly relevant — only candidate retrieves this
            "sku-001": 2,  # relevant in both
            "sku-007": 1,
            "sku-008": 1,
            "sku-009": 0,
            "sku-002": 0,
            "sku-003": 0,
            "sku-004": 0,
            "sku-005": 0,
        },
        "expected_s2n": 2.0,
        "expected_decision": "HOLD",
        "expected_ndcg_improved": True,   # candidate retrieves sku-006; baseline doesn't
    },

    # -----------------------------------------------------------------------
    # ROLLBACK: heavy baseline noise (4 position offsets), candidate adds only
    # 1 new product that is NOT relevant → candidate_diffs=1, noise_diffs=4
    # → S2N = 0.25
    #
    # Qrels: sku-003 and sku-005 are relevant (both in baseline and candidate
    # at the same positions) → no NDCG gain. Regression = False but no improvement.
    # -----------------------------------------------------------------------
    "rollback": {
        "description": (
            "Noisy system, candidate barely changes results. "
            "Expected S2N = 0.25 → ROLLBACK.  No NDCG improvement."
        ),
        "query": "noise cancelling headphones",
        "routes": {
            "baseline-a": ["sku-001", "sku-002", "sku-003", "sku-004", "sku-005"],
            # Heavy reordering: 001↔002 and 003↔004 → 4 position offsets
            "baseline-b": ["sku-002", "sku-001", "sku-004", "sku-003", "sku-005"],
            # Candidate only adds sku-006 (not relevant) → candidate_diffs = 1
            "candidate":  ["sku-001", "sku-002", "sku-003", "sku-004", "sku-005", "sku-006"],
        },
        # sku-003 and sku-005 are relevant — both appear in baseline and candidate.
        # sku-006 added by candidate is irrelevant.
        "qrels": {
            "sku-003": 3,
            "sku-005": 2,
            "sku-001": 1,
            "sku-002": 0,
            "sku-004": 0,
            "sku-006": 0,  # the only new item is not relevant
        },
        "expected_s2n": 0.25,
        "expected_decision": "ROLLBACK",
        "expected_ndcg_improved": False,  # no relevant items gained by candidate
    },
}
