"""
Ranx Evaluator — evaluates e-commerce search results using the ranx library.
"""

import logging
from typing import List, Dict, Any, Optional
from ranx import Qrels, Run, evaluate

from shadow_agent_framework.config.settings import RanxConfig
from shadow_agent_framework.models.schemas import InferenceRequest, InferenceResponse, EvaluationResult, JudgeScore, EvaluationVerdict

logger = logging.getLogger(__name__)


class RanxEvaluator:
    """
    Evaluates e-commerce search results using the ranx library.
    
    Assumes: 
    - Champion response content is the 'ground truth' or baseline list of items.
    - Challenger response content is the 'candidate' list of items.
    - Both contents are lists of dictionaries, each with an 'id' and 'score'/'relevance'.
    """

    def __init__(self, config: RanxConfig):
        self.config = config

    async def evaluate(
        self,
        request: InferenceRequest,
        champion_response: InferenceResponse,
        challenger_response: InferenceResponse,
    ) -> EvaluationResult:
        """Evaluate challenger response against champion response using ranx metrics."""
        try:
            qrels_data = self._parse_response_for_qrels(champion_response)
            run_data = self._parse_response_for_run(challenger_response)

            # If no items to evaluate, return a neutral result
            if not qrels_data or not run_data:
                return self._neutral_result(request.request_id, "No items to evaluate")

            qrels = Qrels.from_dict({"query": qrels_data})
            run = Run.from_dict({"query": run_data})

            # Evaluate using configured metrics
            metrics_results = evaluate(qrels, run, self.config.metrics)

            # Aggregate scores and create JudgeScore objects
            judge_scores: Dict[str, JudgeScore] = {}
            overall_score = 0.0
            for metric, value in metrics_results.items():
                judge_scores[metric] = JudgeScore(
                    dimension=metric,
                    score=value * 10, # Scale to 0-10 for consistency with LLM Judge
                    reasoning=f"Ranx {metric} score: {value}",
                    passed=value >= self.config.pass_threshold, # Use ranx specific threshold
                )
                overall_score += value
            
            # Average overall score
            overall_score = (overall_score / len(self.config.metrics)) * 10 if self.config.metrics else 0.0

            verdict = (
                EvaluationVerdict.PASS
                if overall_score >= self.config.pass_threshold * 10
                else EvaluationVerdict.FAIL
            )

            return EvaluationResult(
                request_id=request.request_id,
                champion_latency_ms=champion_response.latency_ms,
                challenger_latency_ms=challenger_response.latency_ms,
                judge_scores=judge_scores,
                overall_score=overall_score,
                verdict=verdict,
                latency_delta_ms=challenger_response.latency_ms - champion_response.latency_ms,
                token_delta=0, # Ranx doesn't deal with tokens, set to 0
                champion_response=champion_response, # Include responses for full trace
                challenger_response=challenger_response,
            )

        except Exception as e:
            logger.error(f"Ranx evaluation failed for request {request.request_id}: {e}", exc_info=True)
            return self._error_result(request.request_id, str(e))

    def _parse_response_for_qrels(self, response: InferenceResponse) -> Dict[str, float]:
        """Parses champion response content into qrels format (doc_id -> relevance)."""
        qrels = {}
        if isinstance(response.content, list):
            for item in response.content:
                if isinstance(item, dict) and "id" in item and "relevance" in item:
                    qrels[str(item["id"])] = item["relevance"]
        return qrels

    def _parse_response_for_run(self, response: InferenceResponse) -> Dict[str, float]:
        """Parses challenger response content into run format (doc_id -> score)."""
        run = {}
        if isinstance(response.content, list):
            for item in response.content:
                if isinstance(item, dict) and "id" in item and "score" in item:
                    run[str(item["id"])] = item["score"]
        return run

    def _error_result(self, request_id: str, error: str) -> EvaluationResult:
        """Helper to create an error EvaluationResult."""
        return EvaluationResult(
            request_id=request_id,
            verdict=EvaluationVerdict.ERROR,
            overall_score=0.0,
            judge_scores={}, 
            latency_delta_ms=0.0,
            token_delta=0,
            metadata={"error": error}
        )
    
    def _neutral_result(self, request_id: str, message: str) -> EvaluationResult:
        """Helper to create a neutral EvaluationResult when no data to evaluate."""
        return EvaluationResult(
            request_id=request_id,
            verdict=EvaluationVerdict.NEUTRAL,
            overall_score=5.0, # Neutral score
            judge_scores={}, 
            latency_delta_ms=0.0,
            token_delta=0,
            metadata={"error": message}
        )
