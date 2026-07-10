"""
Shadow Testing Agent — Data Schemas
=====================================
Pydantic-style dataclasses for all shadow testing data models.
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class EvaluationVerdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NEUTRAL = "neutral"
    ERROR = "error"


class PromotionStatus(str, Enum):
    HOLD = "hold"
    CANDIDATE = "candidate"
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled_back"


@dataclass
class InferenceRequest:
    """A single inference request to be mirrored."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    messages: List[Dict[str, str]] = field(default_factory=list)
    model_params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class InferenceResponse:
    """Response from a model inference call."""
    request_id: str = ""
    model_name: str = ""
    model_id: str = ""
    content: Any = ""
    usage: Dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    status: RequestStatus = RequestStatus.COMPLETED
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    raw_response: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JudgeScore:
    """Score from the LLM-as-Judge on a single dimension."""
    dimension: str = ""
    score: float = 0.0
    reasoning: str = ""
    passed: bool = False


@dataclass
class EvaluationResult:
    """Full evaluation result comparing champion vs challenger."""
    evaluation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    champion_response: Optional[InferenceResponse] = None
    challenger_response: Optional[InferenceResponse] = None
    judge_scores: Dict[str, JudgeScore] = field(default_factory=dict)  # dimension -> score
    overall_score: float = 0.0
    verdict: EvaluationVerdict = EvaluationVerdict.NEUTRAL
    champion_latency_ms: float = 0.0
    challenger_latency_ms: float = 0.0
    latency_delta_ms: float = 0.0
    champion_tokens: int = 0
    challenger_tokens: int = 0
    token_delta: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class GatingResult:
    """Result of evaluating a gating rule."""
    rule_name: str = ""
    metric: str = ""
    current_value: float = 0.0
    threshold: float = 0.0
    operator: str = ">="
    triggered: bool = False
    action: str = "alert"
    message: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class ShadowTestResult:
    """Aggregated result for a shadow test run."""
    test_name: str = ""
    total_requests: int = 0
    evaluated_requests: int = 0
    champion_avg_score: float = 0.0
    challenger_avg_score: float = 0.0
    score_delta: float = 0.0
    champion_avg_latency_ms: float = 0.0
    challenger_avg_latency_ms: float = 0.0
    latency_delta_ms: float = 0.0
    champion_p99_latency_ms: float = 0.0
    challenger_p99_latency_ms: float = 0.0
    pass_rate: float = 0.0
    fail_rate: float = 0.0
    error_rate: float = 0.0
    gating_results: List[GatingResult] = field(default_factory=list)
    promotion_status: PromotionStatus = PromotionStatus.HOLD
    dimension_scores: Dict[str, Dict[str, float]] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class HumanReviewItem:
    """An item queued for human review."""
    review_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    evaluation_result: Optional[EvaluationResult] = None
    priority: str = "medium"  # low, medium, high, critical
    assigned_to: Optional[str] = None
    status: str = "pending"   # pending, in_review, approved, rejected
    human_verdict: Optional[str] = None
    human_notes: str = ""
    timestamp: float = field(default_factory=time.time)
