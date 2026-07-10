"""
Metrics Collector — aggregates and computes shadow test metrics.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict

from shadow_agent_framework.models.schemas import (
    EvaluationResult,
    EvaluationVerdict,
    ShadowTestResult,
    PromotionStatus,
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and aggregates metrics from shadow test evaluations.
    
    Provides:
    - Running statistics (mean, min, max, percentiles)
    - Per-dimension breakdowns
    - Summary computation
    """

    def __init__(self):
        self._evaluations: List[EvaluationResult] = []
        self._latencies: List[float] = []
        self._champion_latencies: List[float] = []
        self._scores: List[float] = []
        self._dimension_scores: Dict[str, List[float]] = defaultdict(list)
        self._verdicts: Dict[str, int] = defaultdict(int)

    def record(self, result: EvaluationResult) -> None:
        """Record an evaluation result."""
        self._evaluations.append(result)

        if result.overall_score > 0:
            self._scores.append(result.overall_score)

        if result.challenger_latency_ms > 0:
            self._latencies.append(result.challenger_latency_ms)

        if result.champion_latency_ms > 0:
            self._champion_latencies.append(result.champion_latency_ms)

        for dim, score in result.judge_scores.items():
            self._dimension_scores[dim].append(score.score)

        self._verdicts[result.verdict.value] += 1

    def compute_summary(
        self, results: List[EvaluationResult] = None, test_name: str = ""
    ) -> ShadowTestResult:
        """
        Compute a summary ShadowTestResult from recorded or provided evaluations.
        
        Args:
            results: Optional list of evaluations (uses internal buffer if None)
            test_name: Name for the summary result
        """
        evals = results if results is not None else self._evaluations
        total = len(evals)

        # Compute scores
        scores = [e.overall_score for e in evals if e.overall_score > 0]
        challenger_latencies = [e.challenger_latency_ms for e in evals if e.challenger_latency_ms > 0]
        champion_latencies = [e.champion_latency_ms for e in evals if e.champion_latency_ms > 0]

        # Verdict counts
        verdicts: Dict[str, int] = defaultdict(int)
        for e in evals:
            verdicts[e.verdict.value] += 1

        # Score stats
        score_mean = sum(scores) / len(scores) if scores else 0.0

        # Latency stats
        def _percentile(sorted_list: List[float], p: float) -> float:
            if not sorted_list:
                return 0.0
            n = len(sorted_list)
            idx = min(int(n * p / 100), n - 1)
            return sorted_list[idx]

        sorted_chal_lat = sorted(challenger_latencies)
        sorted_champ_lat = sorted(champion_latencies)

        chal_avg = sum(challenger_latencies) / len(challenger_latencies) if challenger_latencies else 0.0
        champ_avg = sum(champion_latencies) / len(champion_latencies) if champion_latencies else 0.0

        # Pass/fail rates
        pass_rate = verdicts.get("pass", 0) / total if total > 0 else 0.0
        fail_rate = verdicts.get("fail", 0) / total if total > 0 else 0.0
        error_rate = verdicts.get("error", 0) / total if total > 0 else 0.0

        return ShadowTestResult(
            test_name=test_name,
            total_requests=total,
            evaluated_requests=total,
            challenger_avg_score=round(score_mean, 4),
            champion_avg_score=round(score_mean, 4),  # Same since judge scores challenger
            score_delta=0.0,
            champion_avg_latency_ms=round(champ_avg, 2),
            challenger_avg_latency_ms=round(chal_avg, 2),
            latency_delta_ms=round(chal_avg - champ_avg, 2),
            champion_p99_latency_ms=round(_percentile(sorted_champ_lat, 99), 2),
            challenger_p99_latency_ms=round(_percentile(sorted_chal_lat, 99), 2),
            pass_rate=round(pass_rate, 4),
            fail_rate=round(fail_rate, 4),
            error_rate=round(error_rate, 4),
            dimension_scores=self.compute_dimension_breakdown(results=evals),
        )

    def compute_dimension_breakdown(
        self, results: List[EvaluationResult] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute per-dimension score breakdowns.
        
        Args:
            results: Optional list of evaluations (uses internal buffer if None)
        """
        evals = results if results is not None else self._evaluations
        dim_scores: Dict[str, List[float]] = defaultdict(list)

        for e in evals:
            for dim, score in e.judge_scores.items():
                dim_scores[dim].append(score.score)

        breakdown = {}
        for dim, scores in dim_scores.items():
            if scores:
                breakdown[dim] = {
                    "mean": round(sum(scores) / len(scores), 4),
                    "min": round(min(scores), 4),
                    "max": round(max(scores), 4),
                    "count": len(scores),
                }
            else:
                breakdown[dim] = {"mean": 0.0, "min": 0.0, "max": 0.0, "count": 0}
        return breakdown

    @property
    def evaluation_count(self) -> int:
        return len(self._evaluations)

    def reset(self) -> None:
        """Reset all collected metrics."""
        self._evaluations.clear()
        self._latencies.clear()
        self._champion_latencies.clear()
        self._scores.clear()
        self._dimension_scores.clear()
        self._verdicts.clear()
