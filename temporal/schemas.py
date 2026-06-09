# temporal/schemas.py
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

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
    GENERATED = "generated"
    AUTO_APPROVED = "auto_approved"

class RunbookApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"

class OpsSignal(BaseModel):
    """
    Represents the initial raw signal detected by the monitoring system.
    Enhanced with flexible fields to aid AI reasoning and root cause analysis.
    """
    signal_id: str = Field(..., description="Unique identifier for the signal.")
    signal_type: str = Field(..., description="The type of signal (e.g., catalog_update_failure).")
    summary: str = Field(..., description="A human-readable summary of the issue.")
    
    # Flexible Metadata Fields
    severity: str = Field("medium", description="CRITICAL, HIGH, MEDIUM, LOW")
    category: Optional[str] = Field(None, description="The logical category (e.g., Electronics, Catalog, Checkout).")
    affected_entities: List[str] = Field(default_factory=list, description="List of IDs or names of affected products/services.")
    
    raw_data: Dict[str, Any] = Field(..., description="The complete, raw JSON object.")
    
    # Allow for any extra fields to be added dynamically
    model_config = {"extra": "allow"}

class RootCauseReport(BaseModel):
    signal_id: str
    root_cause: str = Field(..., description="A precise statement identifying the root cause.")
    affected_capability: str = Field(..., description="The core AI Search capability that is impacted.")
    evidence: List[str] = Field(..., description="A list of file paths or identifiers for evidence.")

class ImpactAnalysis(BaseModel):
    signal_id: str
    business_impact: str = Field(..., description="How the issue affects business metrics.")
    affected_dashboards: List[str] = Field(default_factory=list, description="BI dashboards that will show incorrect data.")
    affected_teams: List[str] = Field(default_factory=list, description="Teams that need to be aware of this issue.")

class PreventionPlan(BaseModel):
    signal_id: str
    missing_data_quality_tests: List[str] = Field(default_factory=list)
    monitoring_gaps: List[str] = Field(default_factory=list)
    documentation_updates: List[str] = Field(default_factory=list)

class EvalReport(BaseModel):
    signal_id: str
    assessment_state: str = Field(..., description="'pass', 'fail', or 'blocked'")
    confidence_score: float
    shadow_metrics: Dict[str, Any] = Field(default_factory=dict, description="Latency, result counts, diffs")
    eval_summary: str

class Runbook(BaseModel):
    runbook_id: str = Field(..., description="A unique ID for the generated runbook.")
    signal: OpsSignal
    root_cause: RootCauseReport
    impact: ImpactAnalysis
    prevention: PreventionPlan
    eval_report: EvalReport
    immediate_fix_plan: List[str] = Field(..., description="The step-by-step guide to fix the issue now.")
    owner: str = Field(..., description="The suggested team or role responsible for executing the fix.")
    approval_required: bool = Field(..., description="Whether a human needs to approve this runbook before execution.")
    status: RunbookStatus = Field(RunbookStatus.DRAFT, description="Current status of the runbook execution.")
    error_message: Optional[str] = Field(None, description="Any error message if the runbook execution failed.")
    feedback_summary: Optional[str] = Field(None, description="A high-level summary of feedback for this runbook.")
    deployment_metrics_snapshot: Optional[Dict[str, Any]] = Field(None, description="Snapshot of metrics observed during canary monitoring.")
    human_review_notes: Optional[str] = Field(None, description="Detailed notes from human reviewers/operators.")
    effectiveness_score: Optional[float] = Field(None, description="A numerical score indicating the runbook's effectiveness.")
