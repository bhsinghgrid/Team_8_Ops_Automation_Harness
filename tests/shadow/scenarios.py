"""
scenarios.py — Predefined test scenarios for shadow evaluation.

Each scenario defines what each OCS route returns so the diff/S2N math
produces a known, predictable result.

S2N thresholds (from CanaryEvaluationAgent):
    >= 5.0  → PROMOTE
    2.0–4.9 → HOLD
    < 2.0   → ROLLBACK
"""

SCENARIOS = {
    # -----------------------------------------------------------------------
    # PROMOTE: baselines are identical (zero noise), candidate adds 5 new
    # products → candidate_diffs=5, noise_diffs=0 → S2N = 5/1 = 5.0
    # -----------------------------------------------------------------------
    "promote": {
        "description": (
            "Stable system (no noise), candidate adds 5 new products. "
            "Expected S2N = 5.0 → PROMOTE"
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
        "expected_s2n": 5.0,
        "expected_decision": "PROMOTE",
    },

    # -----------------------------------------------------------------------
    # HOLD: minor reordering noise (2 position offsets), candidate adds 4 new
    # products → candidate_diffs=4, noise_diffs=2 → S2N = 4/2 = 2.0
    # -----------------------------------------------------------------------
    "hold": {
        "description": (
            "System has minor ordering noise. Candidate adds 4 products. "
            "Expected S2N = 2.0 → HOLD"
        ),
        "query": "ergonomic laptop stand",
        "routes": {
            "baseline-a": ["sku-001", "sku-002", "sku-003", "sku-004", "sku-005"],
            # sku-002/003 swapped → 2 position offsets = noise_diffs = 2
            "baseline-b": ["sku-001", "sku-003", "sku-002", "sku-004", "sku-005"],
            # candidate adds 4 new skus, same ordering for existing items
            "candidate":  [
                "sku-001", "sku-002", "sku-003", "sku-004", "sku-005",
                "sku-006", "sku-007", "sku-008", "sku-009",
            ],
        },
        "expected_s2n": 2.0,
        "expected_decision": "HOLD",
    },

    # -----------------------------------------------------------------------
    # ROLLBACK: heavy baseline noise (4 position offsets), candidate adds
    # only 1 new product → candidate_diffs=1, noise_diffs=4 → S2N = 0.25
    # -----------------------------------------------------------------------
    "rollback": {
        "description": (
            "Noisy system (lots of ordering variance), candidate barely changes "
            "results. Expected S2N = 0.25 → ROLLBACK"
        ),
        "query": "noise cancelling headphones",
        "routes": {
            "baseline-a": ["sku-001", "sku-002", "sku-003", "sku-004", "sku-005"],
            # Heavy reordering: 001↔002 and 003↔004 → 4 position offsets
            "baseline-b": ["sku-002", "sku-001", "sku-004", "sku-003", "sku-005"],
            # Candidate only adds one product → candidate_diffs = 1
            "candidate":  ["sku-001", "sku-002", "sku-003", "sku-004", "sku-005", "sku-006"],
        },
        "expected_s2n": 0.25,
        "expected_decision": "ROLLBACK",
    },
}
