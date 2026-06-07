# Runbook_System_Final/shared/schemas.py
"""Defines the shared data contracts for the runbook pipeline."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class RunbookStatus(str, Enum):
    DRAFT = "draft"
    EVALUATING = "evaluating"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYING = "deploying"
    MONITORING_CANARY = "monitoring_canary"
    PROMOTING_CANARY = "promoting_canary"
    ROLLED_BACK = "rolled_back"
    COMPLETED = "completed"
    FAILED = "failed"

class RunbookApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class OpsSignal(BaseModel):
    """
    Represents the initial raw signal detected by the monitoring system (Phase 1).
    This is the primary input for the entire runbook pipeline.
    """
    signal_id: str = Field(..., description="Unique identifier for the signal, e.g., 'ocs-products-unknown-empty_query'.")
    signal_type: str = Field(..., description="The type of signal, e.g., 'empty_query' or 'low_result_count'.")
    summary: str = Field(..., description="A human-readable summary of the detected issue.")
    raw_data: Dict[str, Any] = Field(..., description="The complete, raw JSON object of the signal for deep analysis.")

class RootCauseReport(BaseModel):
    """
    Output from the RootCauseAgent. It provides a specific diagnosis of the problem.
    """
    signal_id: str
    root_cause: str = Field(..., description="A precise statement identifying the root cause.")
    affected_capability: str = Field(..., description="The core AI Search capability that is impacted.")
    evidence: List[str] = Field(..., description="A list of file paths or identifiers for evidence used in the analysis.")

class ImpactAnalysis(BaseModel):
    """
    Output from the CapabilityImpactAgent. It details the business and operational consequences.
    """
    signal_id: str
    business_impact: str = Field(..., description="How the issue affects business metrics like conversion, CTR, or revenue.")
    affected_dashboards: List[str] = Field(default_factory=list, description="BI dashboards that will show incorrect data.")
    affected_teams: List[str] = Field(default_factory=list, description="Teams that need to be aware of this issue.")

class PreventionPlan(BaseModel):
    """
    Output from the DataGapAgent. It recommends long-term fixes to prevent recurrence.
    """
    signal_id: str
    missing_data_quality_tests: List[str] = Field(default_factory=list)
    monitoring_gaps: List[str] = Field(default_factory=list)
    documentation_updates: List[str] = Field(default_factory=list)

class EvalReport(BaseModel):
    """
    Output from Phase 3: Shadow Testing and Evaluation.
    Provides offline and shadow evidence of the proposed fix.
    """
    signal_id: str
    assessment_state: str = Field(..., description="'pass', 'fail', or 'blocked'")
    confidence_score: float
    shadow_metrics: Dict[str, Any] = Field(default_factory=dict, description="Latency, result counts, diffs")
    eval_summary: str

class Runbook(BaseModel):
    """
    Final output from the FixPlanAgent. This is the comprehensive, actionable plan for operators.
    Enriched with feedback fields for post-execution analysis.
    """
    runbook_id: str = Field(..., description="A unique ID for the generated runbook.")
    signal: OpsSignal
    root_cause: RootCauseReport
    impact: ImpactAnalysis
    prevention: PreventionPlan
    eval_report: EvalReport
    immediate_fix_plan: List[str] = Field(..., description="The step-by-step guide to fix the issue now.")
    owner: str = Field(..., description="The suggested team or role responsible for executing the fix.")
    approval_required: bool = Field(..., description="Whether a human needs to approve this runbook before execution.")
    
    # Feedback and Status Fields
    status: RunbookStatus = Field(RunbookStatus.DRAFT, description="Current status of the runbook execution.")
    error_message: Optional[str] = Field(None, description="Any error message if the runbook execution failed.")
    feedback_summary: Optional[str] = Field(None, description="A high-level summary of feedback for this runbook.")
    deployment_metrics_snapshot: Optional[Dict[str, Any]] = Field(None, description="Snapshot of metrics observed during canary monitoring.")
    human_review_notes: Optional[str] = Field(None, description="Detailed notes from human reviewers/operators.")
    effectiveness_score: Optional[float] = Field(None, description="A numerical score indicating the runbook's effectiveness.")

class CanaryMonitorResult(BaseModel):
    """
    Structured result from the monitor_canary_activity, providing detailed metrics for feedback.
    """
    status: str = Field(..., description="Overall status of the canary monitoring (e.g., SUCCESS, FAILURE_METRIC_DROP).")
    stable_baseline_metrics: Dict[str, Any] = Field(..., description="Metrics from the stable baseline application.")
    canary_observed_metrics: Dict[str, Any] = Field(..., description="Metrics observed during the canary rollout.")
    failed_checks: int = Field(..., description="Number of metric checks that failed thresholds.")
    analysis_details: List[str] = Field(..., description="Details for each failed check, if any.")
