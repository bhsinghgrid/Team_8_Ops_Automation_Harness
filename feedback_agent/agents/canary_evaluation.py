import logging
from typing import Dict, Any

from feedback_agent.agents.base import BaseAgent
from feedback_agent.config import MOCK_MODE


class CanaryEvaluationAgent(BaseAgent):
    """
    Sub-agent 3: CanaryEvaluationAgent
    Performs Diffy shadow test evaluation and applies business guardrails to
    recommend promoting, rolling back, or holding the fix.

    Shadow testing is delegated to ``feedback_agent.shadow.DiffyShadowEvaluator``,
    which writes its own per-evaluation JSON reports and logs to the dedicated
    ``shadow_output/`` directory and ``shadow_testing.log``.
    """

    def run(self, input_data: Dict[str, Any], pipeline_state: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("Evaluating canary results...")

        # 1. Retrieve prior verification and metrics reports
        verification = pipeline_state.get("verification", {})
        metrics = pipeline_state.get("metrics", {})

        # Default rollback values in case of pre-check failures
        if not verification.get("allPassed", False):
            self.logger.warning("Verification failed. Recommending immediate rollback.")
            return {
                "decision": {
                    "action": "ROLLBACK",
                    "confidence": 1.0,
                    "reason": "Verification checks failed. Immediate rollback triggered to prevent production service degradation.",
                    "nextTrafficTier": "0%"
                }
            }

        # 2. Extract Shadow Test Results
        # input.json path: result -> rlmSynthesis -> result -> workAiWindows -> shadow_test -> summary
        result_wrapper = input_data.get("result", {})
        rlm_synthesis = result_wrapper.get("rlmSynthesis", {})
        confidence = rlm_synthesis.get("result", {}).get("confidence", 0.577)

        query = input_data.get("query") or result_wrapper.get("query", "")

        if MOCK_MODE:
            shadow_test = rlm_synthesis.get("result", {}).get("workAiWindows", {}).get("shadow_test", {})
            summary = shadow_test.get("summary", {})
            s2n = summary.get("signalToNoiseRatio", 6.0)
            candidate_diffs = summary.get("candidateResponseDiffCount", 5)
            noise_diffs = summary.get("noiseResponseDiffCount", 1)
        else:
            # Live Shadow Traffic Evaluation
            # Results are written to shadow_output/<timestamp>_<incident_id>.json
            # Logs go to shadow_testing.log via DiffyShadowEvaluator's dedicated handler
            from feedback_agent.shadow import DiffyShadowEvaluator

            # Extract incident_id for report naming (mirrors AuditTrailAgent logic)
            artifact_dir = result_wrapper.get("applyResult", {}).get("artifactDir", "")
            incident_id = ""
            if artifact_dir and "sequential-" in artifact_dir:
                try:
                    incident_id = (
                        "INC-"
                        + artifact_dir.split("sequential-")[1].split("/")[0].split("_")[0]
                        + "-001"
                    )
                except Exception:
                    pass

            evaluator = DiffyShadowEvaluator(parent_logger=self.logger)
            shadow_report = evaluator.evaluate(query, incident_id=incident_id)
            s2n = shadow_report["s2n"]
            candidate_diffs = shadow_report["candidate_diffs"]
            noise_diffs = shadow_report["noise_diffs"]

            if shadow_report.get("output_path"):
                self.logger.info(f"Shadow report saved to: {shadow_report['output_path']}")

        # 3. Check Latency and Relevance Guardrails
        latency_before = metrics.get("latency_p95_ms", {}).get("before", 45.0)
        latency_delta = metrics.get("latency_p95_ms", {}).get("delta", 7.0)
        zero_result_rate_after = metrics.get("zeroResultRate", {}).get("after", 0.0)

        reasons = []
        action = "PROMOTE"
        next_tier = "25%"

        # Guardrail A: Latency degradation (max 25% or 15ms increase)
        latency_increase_ratio = latency_delta / latency_before if latency_before > 0 else 0
        if latency_delta > 15.0 or latency_increase_ratio > 0.25:
            action = "ROLLBACK"
            reasons.append(
                f"Latency regression detected: p95 latency increased by {latency_delta}ms ({latency_increase_ratio:.1%})."
            )

        # Guardrail B: Zero-result rate
        if zero_result_rate_after > 0.1:
            action = "HOLD"
            reasons.append(f"Zero-result rate remains high at {zero_result_rate_after:.1%}.")

        # Guardrail C: Signal-to-noise ratio
        if action == "PROMOTE":
            if s2n >= 5.0:
                next_tier = "25%"
                reasons.append(
                    f"Shadow test s2n ratio is strong ({s2n} >= 5.0) with "
                    f"{candidate_diffs} candidate diffs and {noise_diffs} noise diffs."
                )
            elif 2.0 <= s2n < 5.0:
                action = "HOLD"
                next_tier = "5%"
                reasons.append(
                    f"Shadow test s2n ratio is moderate ({s2n}), holding traffic tier at 5% to collect more telemetry."
                )
            else:
                action = "ROLLBACK"
                next_tier = "0%"
                reasons.append(
                    f"Shadow test s2n ratio is weak ({s2n} < 2.0), indicating insufficient retrieval signal improvement."
                )

        if not reasons:
            reasons.append("All metrics within baseline expectations.")

        reason_str = " ".join(reasons)
        if action == "PROMOTE":
            reason_str = (
                f"All verification checks passed. Zero-result rate eliminated. "
                f"Latency within acceptable bounds. {reason_str}"
            )
        elif action == "ROLLBACK":
            reason_str = f"Rollback recommended. {reason_str}"
        else:
            reason_str = f"Hold recommended. {reason_str}"

        decision_report = {
            "action": action,
            "confidence": float(round(confidence, 3)),
            "reason": reason_str,
            "nextTrafficTier": next_tier,
        }

        self.logger.info(f"Canary evaluation complete. Action={action}, Confidence={confidence:.3f}")
        return {"decision": decision_report}
