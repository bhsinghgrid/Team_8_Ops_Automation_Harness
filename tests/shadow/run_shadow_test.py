#!/usr/bin/env python3
"""
run_shadow_test.py — CLI runner for local shadow pipeline testing.

Usage
-----
    # Run all three scenarios
    python3 tests/shadow/run_shadow_test.py

    # Run a specific scenario
    python3 tests/shadow/run_shadow_test.py --scenario promote
    python3 tests/shadow/run_shadow_test.py --scenario hold
    python3 tests/shadow/run_shadow_test.py --scenario rollback

What happens
------------
For each scenario the runner:
  1. Starts a local mock HTTP server on port 8765 (no OCS connection needed)
  2. Temporarily overrides OCS_SEARCH_URL to point at the mock server
  3. Calls DiffyShadowEvaluator.evaluate() — the REAL live code path
  4. Validates S2N and decision against expected values
  5. Prints a colour-coded summary
  6. Writes the JSON report to tests/shadow/output/ and logs to tests/shadow/output/shadow_testing.log

Run from the project root:
    python3 tests/shadow/run_shadow_test.py
"""

import argparse
import json
import os
import sys

# ── Make sure the package root is on sys.path ───────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Import scenario definitions and server ───────────────────────────────────
from tests.shadow.scenarios import SCENARIOS
from tests.shadow.mock_server import MockOCSServer

# ── ANSI colours ─────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

MOCK_PORT = 8765
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

DECISION_COLOR = {
    "PROMOTE":  GREEN,
    "HOLD":     YELLOW,
    "ROLLBACK": RED,
}


def s2n_to_decision(s2n: float) -> str:
    if s2n >= 5.0:
        return "PROMOTE"
    if s2n >= 2.0:
        return "HOLD"
    return "ROLLBACK"


def run_scenario(name: str, scenario: dict) -> bool:
    """
    Execute one scenario end-to-end.

    Returns True if the result matches expectations, False otherwise.
    """
    print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}Scenario: {name.upper()}{RESET}")
    print(f"  Query   : {scenario['query']}")
    print(f"  Desc    : {scenario['description']}")
    print(f"  Expected: S2N={scenario['expected_s2n']}  Decision={scenario['expected_decision']}")

    # ── Point evaluator at local mock server ─────────────────────────────
    os.environ["OCS_SEARCH_URL"] = f"http://127.0.0.1:{MOCK_PORT}"
    os.environ["SHADOW_OUTPUT_DIR"] = OUTPUT_DIR

    # Re-import config constants so they pick up the env override.
    # (They are module-level strings; we patch them directly on the module.)
    import feedback_agent.config as cfg
    cfg.OCS_SEARCH_URL = f"http://127.0.0.1:{MOCK_PORT}"
    cfg.SHADOW_OUTPUT_DIR = OUTPUT_DIR

    # Also patch the evaluator module which imported these at import time
    import feedback_agent.shadow.evaluator as ev_mod
    ev_mod.OCS_SEARCH_URL = f"http://127.0.0.1:{MOCK_PORT}"
    ev_mod.SHADOW_OUTPUT_DIR = OUTPUT_DIR

    # ── Start the mock server with this scenario's routes ────────────────
    with MockOCSServer(port=MOCK_PORT, routes=scenario["routes"]):
        from feedback_agent.shadow.evaluator import DiffyShadowEvaluator

        evaluator = DiffyShadowEvaluator()
        report = evaluator.evaluate(
            query=scenario["query"],
            incident_id=f"TEST-{name.upper()}",
            qrels=scenario.get("qrels"),   # pass relevance judgments for ranx
        )

    # ── Validate S2N + decision ──────────────────────────────────────────
    actual_s2n      = report["s2n"]
    actual_decision = s2n_to_decision(actual_s2n)
    expected_s2n    = scenario["expected_s2n"]
    expected_dec    = scenario["expected_decision"]

    dec_color = DECISION_COLOR.get(actual_decision, RESET)
    s2n_ok    = (actual_s2n == expected_s2n)
    dec_ok    = (actual_decision == expected_dec)

    # ── Validate ranking metrics (ranx) ──────────────────────────────────
    ranking = report.get("ranking_metrics") or {}
    # 'ndcg@10' lives inside ranking['baseline'] and ranking['candidate']
    # The top-level dict has 'ndcg@10_delta' (the delta key)
    ndcg_key = next(
        (k for k in ranking.get("baseline", {}) if k.startswith("ndcg@")), None
    )
    ndcg_delta     = ranking.get(f"{ndcg_key}_delta") if ndcg_key else None
    mrr_delta      = ranking.get("mrr_delta")
    baseline_ndcg  = ranking.get("baseline", {}).get(ndcg_key) if ndcg_key else None
    cand_ndcg      = ranking.get("candidate", {}).get(ndcg_key) if ndcg_key else None
    expected_ndcg_improved = scenario.get("expected_ndcg_improved")
    ndcg_ok = True
    if expected_ndcg_improved is not None and ndcg_delta is not None:
        ndcg_ok = (ranking.get("improved") == expected_ndcg_improved)

    passed = s2n_ok and dec_ok and ndcg_ok
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"

    print(f"\n  {'S2N Result':12s}: candidate_diffs={report['candidate_diffs']}  "
          f"noise_diffs={report['noise_diffs']}  S2N={actual_s2n}")
    print(f"  {'Decision':12s}: {dec_color}{actual_decision}{RESET}")

    # Ranking metrics block
    if ndcg_key and ndcg_delta is not None:
        trend = f"{GREEN}▲ improved{RESET}" if ranking.get('improved') else (
                f"{RED}▼ regression{RESET}" if ranking.get('regression') else "→ unchanged")
        print(f"  {'NDCG@10':12s}: baseline={baseline_ndcg}  candidate={cand_ndcg}  "
              f"delta={ndcg_delta:+.4f}  {trend}")
        print(f"  {'MRR delta':12s}: {mrr_delta:+.4f}")
    else:
        print(f"  {'Ranking':12s}: no qrels provided (skipped)")

    print(f"  {'Report':12s}: {report.get('output_path', 'N/A')}")
    print(f"  {status}")

    if not s2n_ok:
        print(f"  {RED}S2N: expected {expected_s2n}, got {actual_s2n}{RESET}")
    if not dec_ok:
        print(f"  {RED}Decision: expected {expected_dec}, got {actual_decision}{RESET}")
    if not ndcg_ok:
        print(f"  {RED}NDCG improved: expected {expected_ndcg_improved}, got {ranking.get('improved')}{RESET}")

    return passed


def main():
    parser = argparse.ArgumentParser(description="Run local shadow pipeline tests")
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()) + ["all"],
        default="all",
        help="Which scenario to run (default: all)",
    )
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    to_run = (
        list(SCENARIOS.items())
        if args.scenario == "all"
        else [(args.scenario, SCENARIOS[args.scenario])]
    )

    print(f"\n{BOLD}{'='*60}")
    print("  OCS Shadow Pipeline — Local Test Runner")
    print(f"{'='*60}{RESET}")
    print(f"  Mock server port : {MOCK_PORT}")
    print(f"  Output directory : {OUTPUT_DIR}")
    print(f"  Running          : {[n for n, _ in to_run]}")

    results = {}
    for name, scenario in to_run:
        results[name] = run_scenario(name, scenario)

    # ── Final summary ─────────────────────────────────────────────────────
    print(f"\n{BOLD}{'='*60}")
    print("  Summary")
    print(f"{'='*60}{RESET}")
    all_passed = True
    for name, passed in results.items():
        icon = f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"
        print(f"  {icon}  {name}")
        if not passed:
            all_passed = False

    print()
    log_path = os.path.join(OUTPUT_DIR, "shadow_testing.log")
    if os.path.exists(log_path):
        print(f"  📋 Full log: {log_path}")

    print()
    if all_passed:
        print(f"{GREEN}{BOLD}  All scenarios passed!{RESET}\n")
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}  Some scenarios failed — check output above.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
