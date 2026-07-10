"""
Shadow Testing Agent — Configuration Settings
================================================
Central configuration for the shadow testing framework.
Supports environment variables, config files, and defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class ShadowMode(str, Enum):
    """Shadow test execution modes."""
    ASYNC = "async"        # Fire-and-forget shadow calls (non-blocking)
    SYNC = "sync"          # Wait for shadow results before returning
    HYBRID = "hybrid"      # Async by default, sync for evaluation windows


class EvaluationStrategy(str, Enum):
    """How to evaluate shadow model outputs."""
    LLM_JUDGE = "llm_judge"            # Use an LLM to grade outputs
    RANX = "ranx"                      # Use ranx for ranked list evaluation
    EXACT_MATCH = "exact_match"        # Exact string comparison
    SEMANTIC_SIMILARITY = "semantic"    # Embedding-based similarity
    CUSTOM_HEURISTIC = "custom"        # User-defined scoring function
    HUMAN_REVIEW = "human_review"      # Queue for human review


class GatingAction(str, Enum):
    """Actions when gating rules are triggered."""
    PROMOTE = "promote"        # Auto-promote challenger to champion
    ALERT = "alert"            # Send alert, keep current champion
    ROLLBACK = "rollback"      # Revert to previous champion
    HOLD = "hold"              # Hold current state, no action


@dataclass
class RanxConfig:
    """Configuration for ranx-based e-commerce evaluation."""
    metrics: List[str] = field(default_factory=lambda: ["ndcg@10", "recall@10", "hit_rate@10"])
    pass_threshold: float = 0.7  # Threshold for Ranx metrics (0-1 range)


@dataclass
class ModelConfig:
    """Configuration for a single model (champion or challenger)."""
    name: str
    provider: str = "openai"           # openai, anthropic, azure, local, etc.
    model_id: str = "gpt-4o"          # Model identifier
    api_base: Optional[str] = None     # Custom API endpoint
    api_key_env: str = ""              # Environment variable name for API key
    gemini_api_key_env: Optional[str] = None # Environment variable for Gemini API key
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout_seconds: float = 30.0
    extra_params: Dict = field(default_factory=dict)

    @property
    def api_key(self) -> Optional[str]:
        if self.api_key_env:
            return os.environ.get(self.api_key_env, None)
        return None


@dataclass
class JudgeConfig:
    """Configuration for the LLM-as-Judge evaluator."""
    provider: str = "gemini"
    model_id: str = "gemini-2.5-pro"
    api_key_env: Optional[str] = None
    gemini_api_key_env: Optional[str] = "GEMINI_API_KEY" # Environment variable for Gemini API key
    temperature: float = 0.0          # Deterministic judging
    judge_prompt_template: str = "default"
    score_range: tuple = (0, 10)      # Min and max score
    pass_threshold: float = 7.0       # Score needed to "pass"
    dimensions: List[str] = field(default_factory=lambda: [
        "accuracy", "relevance", "completeness", "clarity", "safety"
    ])

    @property
    def api_key(self) -> Optional[str]:
        if self.provider == "gemini" and self.gemini_api_key_env:
            return os.environ.get(self.gemini_api_key_env, None)
        elif self.api_key_env:
            return os.environ.get(self.api_key_env, None)
        return None


@dataclass
class MLflowConfig:
    """Configuration for MLflow tracing integration."""
    tracking_uri: str = "http://localhost:5000"
    experiment_name: str = "shadow-testing-agent"
    run_name_prefix: str = "shadow-run"
    log_models: bool = True
    log_metrics: bool = True
    log_artifacts: bool = True
    auto_log: bool = True


@dataclass
class RedisConfig:
    """Configuration for Redis storage."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None


@dataclass
class AdaptiveMirroringConfig:
    """Configuration for adaptive traffic mirroring."""
    enabled: bool = False
    min_percentage: float = 10.0      # Minimum traffic to mirror
    max_percentage: float = 100.0     # Maximum traffic to mirror
    # Thresholds based on challenger performance (e.g., if avg_score drops below this, increase mirroring)
    performance_threshold_increase_mirror: float = 0.6  # Example: 60% pass rate
    performance_threshold_decrease_mirror: float = 0.9  # Example: 90% pass rate
    adjustment_step: float = 5.0      # Percentage points to adjust by
    check_interval_minutes: int = 5   # How often to check metrics for adjustment


@dataclass
class GatingRule:
    """A single gating rule for promotion/rollback decisions."""
    name: str
    metric: str                        # e.g., "accuracy", "latency_p99"
    operator: str = ">="               # >, <, >=, <=, ==, !=
    threshold: float = 0.0
    action: GatingAction = GatingAction.ALERT
    window_size: int = 100             # Number of samples to evaluate
    cooldown_minutes: int = 60         # Minimum time between actions


@dataclass
class ShadowTestConfig:
    """Master configuration for a shadow test."""
    test_name: str = "default-shadow-test"
    mode: ShadowMode = ShadowMode.ASYNC
    shadow_traffic_percentage: float = 100.0   # % of traffic to mirror (0-100)
    max_concurrent_shadows: int = 10
    evaluation_strategy: EvaluationStrategy = EvaluationStrategy.LLM_JUDGE
    champion: ModelConfig = field(default_factory=lambda: ModelConfig(name="champion"))
    challengers: List[ModelConfig] = field(default_factory=list)
    judge: JudgeConfig = field(default_factory=JudgeConfig)
    ranx_config: RanxConfig = field(default_factory=RanxConfig) # New ranx config
    mlflow: MLflowConfig = field(default_factory=MLflowConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    adaptive_mirroring: AdaptiveMirroringConfig = field(default_factory=AdaptiveMirroringConfig)
    gating_rules: List[GatingRule] = field(default_factory=list)
    alert_webhooks: List[str] = field(default_factory=list)
    sample_rate: float = 1.0          # Fraction of requests to shadow (0-1)
    max_latency_ms: float = 5000.0    # Max acceptable latency for shadow
    enable_human_review_queue: bool = False
    human_review_sample_rate: float = 0.05  # 5% of results queued for review
    retention_days: int = 90          # How long to keep shadow test data

    def __post_init__(self):
        if not self.challengers:
            self.challengers = [
                ModelConfig(name="challenger-v1", model_id="gpt-4o-mini")
            ]
        if not self.gating_rules:
            self.gating_rules = [
                GatingRule(
                    name="accuracy-gate",
                    metric="judge_score_avg",
                    operator=">=",
                    threshold=self.judge.pass_threshold,
                    action=GatingAction.PROMOTE,
                    window_size=100,
                ),
                GatingRule(
                    name="latency-gate",
                    metric="latency_p99_ms",
                    operator="<=",
                    threshold=self.max_latency_ms,
                    action=GatingAction.ALERT,
                    window_size=100,
                ),
            ]
