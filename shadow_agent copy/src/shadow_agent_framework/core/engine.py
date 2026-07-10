"""
Shadow Testing Agent — Core Engine
====================================
The central orchestrator that coordinates traffic mirroring,
model inference, evaluation, gating, and tracing.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Coroutine
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

from shadow_agent_framework.config.settings import (
    ShadowTestConfig,
    ShadowMode,
    GatingAction,
    EvaluationStrategy, # Added EvaluationStrategy
)
from shadow_agent_framework.models.schemas import (
    InferenceRequest,
    InferenceResponse,
    EvaluationResult,
    GatingResult,
    ShadowTestResult,
    PromotionStatus,
    RequestStatus,
    EvaluationVerdict,
    HumanReviewItem, # New import
)
from ..router.traffic_mirror import TrafficMirror
from ..router.model_client import ModelClient
from ..evaluators.judge import LLMJudge
from ..evaluators.comparator import ResponseComparator
from ..evaluators.gating_engine import GatingEngine
from ..evaluators.ranx_evaluator import RanxEvaluator # New import
from ..tracing.mlflow_tracer import MLflowTracer
from ..utils.metrics_collector import MetricsCollector
from ..utils.storage import ShadowTestStorage

logger = logging.getLogger(__name__)


def async_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    A decorator for retrying an async function with exponential backoff.
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (
                    # Add common, transient API errors here
                    asyncio.TimeoutError,
                    # e.g., aiohttp.ClientConnectorError, openai.APITimeoutError
                ) as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries.")
                        raise
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}. "
                        f"Retrying in {current_delay:.2f} seconds. Error: {e}"
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator


class ShadowTestEngine:
    """
    Core shadow testing engine.
    
    Orchestrates the full shadow testing lifecycle:
    1. Receive/mirror production traffic
    2. Route to champion + challenger models
    3. Collect responses with latency tracking
    4. Evaluate via LLM-as-Judge
    5. Compare and score
    6. Check gating rules
    7. Log traces to MLflow
    8. Report results
    """

    def __init__(self, config: ShadowTestConfig):
        self.config = config
        self.traffic_mirror = TrafficMirror(config)
        self.model_client = ModelClient()
        
        if config.evaluation_strategy == EvaluationStrategy.LLM_JUDGE:
            self.evaluator = LLMJudge(config.judge)
        elif config.evaluation_strategy == EvaluationStrategy.RANX:
            self.evaluator = RanxEvaluator(config.ranx_config)
        else:
            raise ValueError(f"Unsupported evaluation strategy: {config.evaluation_strategy}")

        self.comparator = ResponseComparator()
        self.gating_engine = GatingEngine(config.gating_rules)
        self.tracer = MLflowTracer(config.mlflow)
        self.metrics = MetricsCollector()
        self.storage = ShadowTestStorage(config.redis)
        self._executor = ThreadPoolExecutor(max_workers=config.max_concurrent_shadows)
        self._running = False
        self._results_buffer: List[EvaluationResult] = []
        self._lock = asyncio.Lock()

    async def start(self):
        """Initialize the shadow test engine and all subsystems."""
        logger.info(f"Starting shadow test engine: {self.config.test_name}")
        self._running = True
        await self.tracer.initialize()
        await self.storage.initialize()
        logger.info(
            f"Shadow mode: {self.config.mode.value} | "
            f"Traffic %: {self.config.shadow_traffic_percentage} | "
            f"Champion: {self.config.champion.name} | "
            f"Challengers: {[c.name for c in self.config.challengers]}"
        )

    async def stop(self):
        """Gracefully shutdown the engine."""
        logger.info("Stopping shadow test engine...")
        self._running = False
        self._executor.shutdown(wait=True)
        await self.tracer.shutdown()
        await self.storage.close()
        logger.info("Shadow test engine stopped.")

    async def process_request(self, request: InferenceRequest) -> Optional[InferenceResponse]:
        """
        Main entry point: process a production request through the shadow pipeline.
        
        1. Serve the user with the champion model (production path)
        2. Mirror the request to challenger(s) in the background
        3. Evaluate and compare when shadow results are ready
        """
        if not self._running:
            logger.warning("Engine not running, skipping request.")
            return None

        # Check if this request should be shadowed (sampling)
        if not self.traffic_mirror.should_mirror(request):
            # Just route to champion, no shadow
            return await self._call_model(self.config.champion, request)

        # --- PRODUCTION PATH: Call champion model ---
        champion_response = await self._call_model(self.config.champion, request)

        # --- SHADOW PATH: Mirror to challengers ---
        if self.config.mode == ShadowMode.ASYNC:
            # Fire-and-forget: evaluate in background
            asyncio.create_task(
                self._shadow_evaluate_async(request, champion_response)
            )
        elif self.config.mode == ShadowMode.SYNC:
            # Wait for shadow evaluation before returning
            await self._shadow_evaluate_sync(request, champion_response)
        elif self.config.mode == ShadowMode.HYBRID:
            # Async by default, but can switch to sync during eval windows
            asyncio.create_task(
                self._shadow_evaluate_async(request, champion_response)
            )

        return champion_response

    @async_retry()
    async def _call_model(
        self, model_config, request: InferenceRequest
    ) -> InferenceResponse:
        """Call a model with the given request and track latency."""
        start_time = time.time()
        try:
            # Add a timeout to the model call
            response = await asyncio.wait_for(
                self.model_client.call(model_config, request),
                timeout=self.config.max_latency_ms / 1000.0
            )
            response.latency_ms = (time.time() - start_time) * 1000
            return response
        except asyncio.TimeoutError:
            logger.error(f"Model call timed out for {model_config.name} after {self.config.max_latency_ms}ms")
            return InferenceResponse(
                request_id=request.request_id,
                model_name=model_config.name,
                model_id=model_config.model_id,
                status=RequestStatus.TIMEOUT,
                error="Model call timed out",
                latency_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e: # Catch other potential API errors
            logger.error(f"Model call failed for {model_config.name}: {e}", exc_info=True)
            return InferenceResponse(
                request_id=request.request_id,
                model_name=model_config.name,
                model_id=model_config.model_id,
                status=RequestStatus.FAILED,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )

    async def _shadow_evaluate_async(
        self,
        request: InferenceRequest,
        champion_response: InferenceResponse,
    ):
        """Background shadow evaluation (async mode)."""
        try:
            await self._run_shadow_pipeline(request, champion_response)
        except Exception as e:
            logger.error(f"Shadow evaluation failed: {e}", exc_info=True)

    async def _shadow_evaluate_sync(
        self,
        request: InferenceRequest,
        champion_response: InferenceResponse,
    ):
        """Synchronous shadow evaluation — blocks until complete."""
        await self._run_shadow_pipeline(request, champion_response)

    async def _run_shadow_pipeline(
        self,
        request: InferenceRequest,
        champion_response: InferenceResponse,
    ):
        """
        Full shadow testing pipeline for a single request:
        1. Call all challenger models
        2. Evaluate each challenger vs champion
        3. Log traces to MLflow
        4. Check gating rules
        5. Store results
        """
        for challenger_config in self.config.challengers:
            # Call challenger model
            challenger_response = await self._call_model(challenger_config, request)

            # Skip evaluation if challenger failed
            if challenger_response.status == RequestStatus.FAILED:
                logger.warning(
                    f"Challenger {challenger_config.name} failed, skipping evaluation."
                )
                continue

            # Evaluate: LLM-as-Judge comparison or Ranx evaluation
            evaluation = await self.evaluator.evaluate(
                request=request,
                champion_response=champion_response,
                challenger_response=challenger_response,
            )

            # Compare responses (structural/semantic comparison)
            comparison = self.comparator.compare(
                champion_response, challenger_response
            )
            evaluation.metadata["comparison"] = comparison

            # Log trace to MLflow
            await self.tracer.log_shadow_trace(
                request=request,
                champion_response=champion_response,
                challenger_response=challenger_response,
                evaluation=evaluation,
            )

            # Record metrics
            self.metrics.record(evaluation)

            # Store result
            await self.storage.store_evaluation(evaluation)

            # Queue for human review if enabled and conditions met
            if self.config.enable_human_review_queue and self._should_queue_for_human_review(evaluation):
                review_item = HumanReviewItem(
                    evaluation_result=evaluation,
                    priority="high" if evaluation.verdict in [EvaluationVerdict.ERROR, EvaluationVerdict.FAIL] else "medium",
                    status="pending"
                )
                await self.storage.store_human_review_item(review_item)
                logger.info(f"Queued evaluation {evaluation.evaluation_id} for human review (verdict: {evaluation.verdict.value}, score: {evaluation.overall_score:.2f})")

            # Buffer result for gating checks
            async with self._lock:
                self._results_buffer.append(evaluation)

        # Check gating rules periodically
        async with self._lock:
            if len(self._results_buffer) >= self._get_min_window_size():
                await self._check_gates()
                self._results_buffer.clear()

    async def _check_gates(self):
        """Evaluate all gating rules against accumulated results."""
        if not self._results_buffer:
            return

        gating_results = self.gating_engine.evaluate(self._results_buffer)

        for result in gating_results:
            if result.triggered:
                logger.warning(
                    f"🚨 Gating rule triggered: {result.rule_name} | "
                    f"{result.metric} {result.operator} {result.threshold} "
                    f"(current: {result.current_value}) | Action: {result.action}"
                )
                await self.tracer.log_gating_event(result)

                if result.action == GatingAction.PROMOTE.value:
                    await self._handle_promotion(result)
                elif result.action == GatingAction.ROLLBACK.value:
                    await self._handle_rollback(result)
                elif result.action == GatingAction.ALERT.value:
                    await self._handle_alert(result)

    async def _handle_promotion(self, gating_result: GatingResult):
        """Handle a promotion gating action."""
        logger.info(
            f"✅ PROMOTION triggered by {gating_result.rule_name}. "
            f"Challenger meets criteria for promotion."
        )
        # In production, this would trigger a deployment pipeline
        await self.storage.store_gating_event(gating_result, PromotionStatus.CANDIDATE)

    async def _handle_rollback(self, gating_result: GatingResult):
        """Handle a rollback gating action."""
        logger.warning(
            f"⚠️ ROLLBACK triggered by {gating_result.rule_name}. "
            f"Challenger does not meet criteria."
        )
        await self.storage.store_gating_event(gating_result, PromotionStatus.ROLLED_BACK)

    async def _handle_alert(self, gating_result: GatingResult):
        """Handle an alert gating action."""
        logger.info(
            f"🔔 ALERT from {gating_result.rule_name}: {gating_result.message}"
        )
        await self.storage.store_gating_event(gating_result, PromotionStatus.HOLD)

    def _get_min_window_size(self) -> int:
        """Get the minimum window size across all gating rules."""
        if not self.config.gating_rules:
            return 100
        return min(rule.window_size for rule in self.config.gating_rules)

    async def get_results_summary(self) -> ShadowTestResult:
        """Get aggregated results for the current shadow test."""
        all_results = await self.storage.get_all_evaluations(self.config.test_name)
        return self.metrics.compute_summary(all_results, self.config.test_name)

    async def get_dimension_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Get per-dimension score breakdown for champion vs challenger."""
        all_results = await self.storage.get_all_evaluations(self.config.test_name)
        return self.metrics.compute_dimension_breakdown(all_results)

    def _should_queue_for_human_review(self, evaluation: EvaluationResult) -> bool:
        """
        Determines if an evaluation result should be queued for human review.
        Prioritizes neutral verdicts, errors, or low scores.
        """
        # Always queue errors or explicit failures
        if evaluation.verdict in [EvaluationVerdict.ERROR, EvaluationVerdict.FAIL]:
            return True

        # Queue neutral verdicts for deeper inspection
        if evaluation.verdict == EvaluationVerdict.NEUTRAL:
            return True

        # Queue if overall score is below a certain threshold (e.g., if passes are barely passing)
        # Using judge.pass_threshold as a proxy for low score for now
        if evaluation.overall_score < self.config.judge.pass_threshold:
            return True

        # Random sampling for remaining cases (if configured)
        if random.random() < self.config.human_review_sample_rate:
            return True

        return False
