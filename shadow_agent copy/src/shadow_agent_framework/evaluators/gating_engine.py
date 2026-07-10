"""
Gating Engine — evaluates gating rules against accumulated results.
"""

import logging
from typing import List

from ..config.settings import GatingRule, GatingAction
from ..models.schemas import EvaluationResult, GatingResult

logger = logging.getLogger(__name__)


class GatingEngine:
    """
    Evaluates gating rules against accumulated shadow test results.
    
    Determines whether a challenger should be promoted, an alert raised,
    or a rollback initiated based on configurable thresholds.
    """

    def __init__(self, rules: List[GatingRule]):
        self.rules = rules

    def evaluate(self, results: List[EvaluationResult]) -> List[GatingResult]:
        """
        Evaluate all gating rules against the provided results.
        
        Returns a list of GatingResult for each rule that was evaluated.
        """
        gating_results = []

        for rule in self.rules:
            current_value = self._compute_metric(rule.metric, results)
            triggered = self._check_threshold(
                current_value, rule.operator, rule.threshold
            )

            result = GatingResult(
                rule_name=rule.name,
                metric=rule.metric,
                current_value=round(current_value, 4),
                threshold=rule.threshold,
                operator=rule.operator,
                triggered=triggered,
                action=rule.action.value if triggered else "none",
                message=self._build_message(rule, current_value, triggered),
            )
            gating_results.append(result)

            if triggered:
                logger.info(
                    f"Gate '{rule.name}' triggered: {rule.metric} = "
                    f"{current_value:.4f} {rule.operator} {rule.threshold}"
                )

        return gating_results

    def _compute_metric(self, metric: str, results: List[EvaluationResult]) -> float:
        """Compute the value of a named metric from the results."""
        if not results:
            return 0.0

        valid_results = [r for r in results if r.verdict.value != "error"]
        if not valid_results:
            return 0.0

        if metric == "judge_score_avg":
            scores = [r.overall_score for r in valid_results if r.overall_score > 0]
            return sum(scores) / len(scores) if scores else 0.0

        elif metric == "pass_rate":
            passed = sum(1 for r in valid_results if r.verdict.value == "pass")
            return passed / len(valid_results)

        elif metric == "fail_rate":
            failed = sum(1 for r in valid_results if r.verdict.value == "fail")
            return failed / len(valid_results)

        elif metric == "latency_avg_ms":
            latencies = [r.challenger_latency_ms for r in valid_results if r.challenger_latency_ms > 0]
            return sum(latencies) / len(latencies) if latencies else 0.0

        elif metric == "latency_p99_ms":
            latencies = sorted(
                r.challenger_latency_ms for r in valid_results if r.challenger_latency_ms > 0
            )
            if not latencies:
                return 0.0
            idx = int(len(latencies) * 0.99)
            return latencies[min(idx, len(latencies) - 1)]

        elif metric == "latency_delta_ms":
            deltas = [r.latency_delta_ms for r in valid_results]
            return sum(deltas) / len(deltas) if deltas else 0.0

        elif metric == "token_delta":
            deltas = [r.token_delta for r in valid_results]
            return sum(deltas) / len(deltas) if deltas else 0.0

        else:
            logger.warning(f"Unknown metric: {metric}")
            return 0.0

    def _check_threshold(self, value: float, operator: str, threshold: float) -> bool:
        """Check if a value meets the threshold condition."""
        ops = {
            ">": lambda v, t: v > t,
            "<": lambda v, t: v < t,
            ">=": lambda v, t: v >= t,
            "<=": lambda v, t: v <= t,
            "==": lambda v, t: v == t,
            "!=": lambda v, t: v != t,
        }
        check = ops.get(operator, lambda v, t: False)
        return check(value, threshold)

    def _build_message(self, rule: GatingRule, current: float, triggered: bool) -> str:
        """Build a human-readable message for the gating result."""
        if triggered:
            return (
                f"Gating rule '{rule.name}' TRIGGERED: "
                f"{rule.metric} = {current:.4f} {rule.operator} {rule.threshold}. "
                f"Action: {rule.action.value}"
            )
        return (
            f"Gating rule '{rule.name}' OK: "
            f"{rule.metric} = {current:.4f} (threshold: {rule.operator} {rule.threshold})"
        )
