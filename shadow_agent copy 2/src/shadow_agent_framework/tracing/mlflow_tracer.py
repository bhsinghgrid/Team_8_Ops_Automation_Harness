"""
MLflow Tracer — logs shadow test traces and gating events to MLflow.
"""

import logging
from typing import Optional, Dict, Any

from shadow_agent_framework.config.settings import MLflowConfig
from shadow_agent_framework.models.schemas import InferenceRequest, InferenceResponse, EvaluationResult, GatingResult

logger = logging.getLogger(__name__)


class MLflowTracer:
    """
    Traces shadow test runs using MLflow.
    
    Logs:
    - Shadow test evaluations as MLflow runs
    - Gating events as metrics
    - Per-request traces as parameters/tags
    """

    def __init__(self, config: MLflowConfig):
        self.config = config
        self._mlflow = None
        self._client = None
        self._experiment_id = None
        self._active_run = None

    async def initialize(self) -> None:
        """Initialize MLflow connection and experiment."""
        try:
            import mlflow
            from mlflow import MlflowClient

            self._mlflow = mlflow
            mlflow.set_tracking_uri(self.config.tracking_uri)

            self._client = MlflowClient(tracking_uri=self.config.tracking_uri)

            # Get or create experiment
            experiment = mlflow.get_experiment_by_name(self.config.experiment_name)
            if experiment is None:
                self._experiment_id = mlflow.create_experiment(self.config.experiment_name)
            else:
                self._experiment_id = experiment.experiment_id

            logger.info(
                f"MLflow initialized: uri={self.config.tracking_uri}, "
                f"experiment={self.config.experiment_name}"
            )
        except ImportError:
            logger.warning("mlflow not installed — tracing will be no-op")
        except Exception as e:
            logger.error(f"Failed to initialize MLflow: {e}")

    async def shutdown(self) -> None:
        """Clean up MLflow resources."""
        if self._active_run and self._mlflow:
            try:
                self._mlflow.end_run()
            except Exception:
                pass
        self._active_run = None

    async def log_shadow_trace(
        self,
        request: InferenceRequest,
        champion_response: InferenceResponse,
        challenger_response: InferenceResponse,
        evaluation: EvaluationResult,
    ) -> None:
        """Log a single shadow evaluation trace to MLflow."""
        if not self._mlflow:
            return

        try:
            with self._mlflow.start_run(
                experiment_id=self._experiment_id,
                run_name=f"shadow_{evaluation.request_id[:16]}",
                nested=True,
            ):
                # Log metrics
                self._mlflow.log_metric("overall_score", evaluation.overall_score)
                self._mlflow.log_metric("champion_latency_ms", evaluation.champion_latency_ms)
                self._mlflow.log_metric("challenger_latency_ms", evaluation.challenger_latency_ms)
                self._mlflow.log_metric("latency_delta_ms", evaluation.latency_delta_ms)
                self._mlflow.log_metric("token_delta", evaluation.token_delta)

                # Log per-dimension scores
                for dim, score in evaluation.judge_scores.items():
                    self._mlflow.log_metric(f"judge_{dim}", score.score)

                # Log tags
                self._mlflow.set_tag("request_id", evaluation.request_id)
                self._mlflow.set_tag("verdict", evaluation.verdict.value)
                self._mlflow.set_tag("champion_model", champion_response.model_name)
                self._mlflow.set_tag("challenger_model", challenger_response.model_name)

        except Exception as e:
            logger.error(f"Failed to log shadow trace: {e}")

    async def log_gating_event(self, gating_result: GatingResult) -> None:
        """Log a gating event to MLflow."""
        if not self._mlflow:
            return

        try:
            with self._mlflow.start_run(
                experiment_id=self._experiment_id,
                run_name=f"gate_{gating_result.rule_name}",
                nested=True,
            ):
                self._mlflow.log_metric(
                    f"gating_{gating_result.metric}",
                    gating_result.current_value,
                )
                self._mlflow.set_tag("rule_name", gating_result.rule_name)
                self._mlflow.set_tag("triggered", str(gating_result.triggered))
                self._mlflow.set_tag("action", str(gating_result.action))

        except Exception as e:
            logger.error(f"Failed to log gating event: {e}")

    async def log_batch_summary(self, summary: Dict[str, Any]) -> None:
        """Log a batch summary of shadow test results."""
        if not self._mlflow:
            return

        try:
            with self._mlflow.start_run(
                experiment_id=self._experiment_id,
                run_name="batch_summary",
                nested=True,
            ):
                for key, value in summary.items():
                    if isinstance(value, (int, float)):
                        self._mlflow.log_metric(key, value)
                    else:
                        self._mlflow.set_tag(key, str(value))

        except Exception as e:
            logger.error(f"Failed to log batch summary: {e}")
