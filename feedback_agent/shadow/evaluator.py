"""
DiffyShadowEvaluator
--------------------
Executes Diffy-style shadow traffic comparison against the OCS Search API.

Result persistence
~~~~~~~~~~~~~~~~~~
Every call to ``evaluate()`` writes a timestamped JSON report to
``shadow_output/shadow_<timestamp>.json`` inside the project root.
All shadow-specific log lines go to ``shadow_testing.log`` (a dedicated
file handler is added the first time an evaluator is created).
"""

import json
import logging
import os
import datetime
from typing import List

from feedback_agent.config import (
    OCS_SEARCH_URL,
    OCS_SHADOW_ROUTING_HEADER,
    OCS_SHADOW_BASELINE_A,
    OCS_SHADOW_BASELINE_B,
    OCS_SHADOW_CANDIDATE,
    SHADOW_OUTPUT_DIR,
)

# ---------------------------------------------------------------------------
# Dedicated shadow logger
# ---------------------------------------------------------------------------
_SHADOW_LOGGER_NAME = "feedback_agent.shadow"


def _get_shadow_logger() -> logging.Logger:
    """Return (and lazily configure) the dedicated shadow logger."""
    logger = logging.getLogger(_SHADOW_LOGGER_NAME)
    if not logger.handlers:
        # File handler — shadow_testing.log lives INSIDE shadow_output/
        os.makedirs(SHADOW_OUTPUT_DIR, exist_ok=True)
        fh = logging.FileHandler(
            os.path.join(SHADOW_OUTPUT_DIR, "shadow_testing.log"),
            mode="a",
            encoding="utf-8",
        )
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.setLevel(logging.DEBUG)
    return logger


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------
class DiffyShadowEvaluator:
    """
    Executes Diffy-style shadow traffic comparison.

    For each evaluation:
    1. Sends three parallel-style HTTP calls to the OCS Search API with
       different routing headers: ``baseline-a``, ``baseline-b``, and
       ``candidate``.
    2. Computes structural diffs (symmetric set diff + ranking offsets).
    3. Derives the Signal-to-Noise Ratio (S2N).
    4. Writes the full report to ``shadow_output/shadow_<timestamp>.json``.

    Parameters
    ----------
    parent_logger:
        Optional external logger; shadow lines are always *also* written to
        the dedicated ``shadow_testing.log`` file.
    """

    def __init__(self, parent_logger: logging.Logger | None = None):
        self._shadow_logger = _get_shadow_logger()
        self._parent_logger = parent_logger  # may be None

    def _log(self, level: str, msg: str) -> None:
        getattr(self._shadow_logger, level)(msg)
        if self._parent_logger:
            getattr(self._parent_logger, level)(msg)

    # ------------------------------------------------------------------
    # HTTP query
    # ------------------------------------------------------------------
    def query_shadow_target(self, query: str, route_value: str) -> List[str]:
        """
        POST a search request to OCS with the given routing header value.
        Returns a list of product ID strings from the response.
        """
        import requests

        url = f"{OCS_SEARCH_URL}/search-api/v1/search"
        headers = {OCS_SHADOW_ROUTING_HEADER: route_value}
        try:
            self._log("info", f"[Shadow] Querying route='{route_value}' for query='{query}'")
            resp = requests.post(url, json={"q": query}, headers=headers, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                pids = []
                for r in data.get("results", []):
                    if isinstance(r, dict):
                        pid = r.get("id") or r.get("productId")
                        if pid:
                            pids.append(str(pid))
                return pids
            else:
                self._log(
                    "warning",
                    f"[Shadow] Route '{route_value}' returned HTTP {resp.status_code}",
                )
                return []
        except Exception as exc:
            self._log("warning", f"[Shadow] Request to '{route_value}' failed: {exc}")
            return []

    # ------------------------------------------------------------------
    # Diff algorithm (mirrors Diffy's structural comparison)
    # ------------------------------------------------------------------
    def diff_responses(self, resp_a: List[str], resp_b: List[str]) -> int:
        """
        Compute a structural diff score between two ordered response lists.

        Score = (symmetric set difference count) + (sum of ranking offsets
        for items present in both lists).
        """
        set_a = set(resp_a)
        set_b = set(resp_b)
        mismatches = len(set_a ^ set_b)

        position_offsets = 0
        for item in set_a & set_b:
            try:
                position_offsets += abs(resp_a.index(item) - resp_b.index(item))
            except ValueError:
                pass

        return mismatches + position_offsets

    # ------------------------------------------------------------------
    # Orchestrate + persist
    # ------------------------------------------------------------------
    def evaluate(self, query: str, incident_id: str = "") -> dict:
        """
        Run the full Diffy-style shadow evaluation for *query*.

        Results are written to::

            shadow_output/shadow_<YYYYMMDD_HHMMSS>_<incident_id>.json

        Returns a dict with keys ``s2n``, ``candidate_diffs``,
        ``noise_diffs``, ``baseline_a_results``, ``baseline_b_results``,
        ``candidate_results``, ``timestamp``, and ``output_path``.
        """
        self._log("info", f"[Shadow] Starting evaluation for query='{query}' incident='{incident_id}'")

        resp_a = self.query_shadow_target(query, OCS_SHADOW_BASELINE_A)
        resp_b = self.query_shadow_target(query, OCS_SHADOW_BASELINE_B)

        # Noise-calibration fallback: if baseline-b is dead, re-query baseline-a
        if not resp_b:
            self._log(
                "info",
                "[Shadow] Baseline B empty — using second Baseline A call for noise calibration.",
            )
            resp_b = self.query_shadow_target(query, OCS_SHADOW_BASELINE_A)

        resp_cand = self.query_shadow_target(query, OCS_SHADOW_CANDIDATE)

        candidate_diffs = self.diff_responses(resp_a, resp_cand)
        noise_diffs = self.diff_responses(resp_a, resp_b)
        s2n = round(float(candidate_diffs) / float(max(1, noise_diffs)), 2)

        self._log(
            "info",
            f"[Shadow] Result: candidate_diffs={candidate_diffs}, "
            f"noise_diffs={noise_diffs}, S2N={s2n}",
        )

        timestamp = datetime.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{incident_id}" if incident_id else ""
        filename = f"shadow_{timestamp}{suffix}.json"

        report = {
            "query": query,
            "incident_id": incident_id,
            "timestamp": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "baseline_a_results": resp_a,
            "baseline_b_results": resp_b,
            "candidate_results": resp_cand,
            "candidate_diffs": candidate_diffs,
            "noise_diffs": noise_diffs,
            "s2n": s2n,
        }

        os.makedirs(SHADOW_OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(SHADOW_OUTPUT_DIR, filename)
        try:
            with open(output_path, "w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2)
            self._log("info", f"[Shadow] Report saved → {output_path}")
            report["output_path"] = output_path
        except Exception as exc:
            self._log("error", f"[Shadow] Could not write report to {output_path}: {exc}")
            report["output_path"] = None

        return report

    def evaluate_mock(
        self,
        query: str,
        incident_id: str = "",
        baseline_a: list | None = None,
        baseline_b: list | None = None,
        candidate: list | None = None,
    ) -> dict:
        """
        Run the Diffy diff algorithm on supplied (or default) product-ID lists
        WITHOUT making any HTTP calls.  Useful for local testing and CI.

        Writes the same shadow_output JSON report and shadow_testing.log entries
        as the live ``evaluate()`` method.
        """
        resp_a = baseline_a or ["sku-001", "sku-002", "sku-003"]
        resp_b = baseline_b or ["sku-001", "sku-002", "sku-003"]
        resp_cand = candidate or ["sku-001", "sku-002", "sku-003", "sku-004", "sku-005"]

        self._log(
            "info",
            f"[Shadow][MOCK] evaluate_mock called — query='{query}' incident='{incident_id}'",
        )

        candidate_diffs = self.diff_responses(resp_a, resp_cand)
        noise_diffs = self.diff_responses(resp_a, resp_b)
        s2n = round(float(candidate_diffs) / float(max(1, noise_diffs)), 2)

        self._log(
            "info",
            f"[Shadow][MOCK] candidate_diffs={candidate_diffs}, noise_diffs={noise_diffs}, S2N={s2n}",
        )

        import datetime
        timestamp = datetime.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{incident_id}" if incident_id else ""
        filename = f"shadow_mock_{timestamp}{suffix}.json"

        report = {
            "query": query,
            "incident_id": incident_id,
            "mode": "MOCK",
            "timestamp": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "baseline_a_results": resp_a,
            "baseline_b_results": resp_b,
            "candidate_results": resp_cand,
            "candidate_diffs": candidate_diffs,
            "noise_diffs": noise_diffs,
            "s2n": s2n,
        }

        os.makedirs(SHADOW_OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(SHADOW_OUTPUT_DIR, filename)
        try:
            import json as _json
            with open(output_path, "w", encoding="utf-8") as fh:
                _json.dump(report, fh, indent=2)
            self._log("info", f"[Shadow][MOCK] Report saved → {output_path}")
            report["output_path"] = output_path
        except Exception as exc:
            self._log("error", f"[Shadow][MOCK] Could not write report: {exc}")
            report["output_path"] = None

        return report
