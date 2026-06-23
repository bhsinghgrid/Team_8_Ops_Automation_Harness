from pydantic import BaseModel

from .config import TEMPORAL_APPROVAL_STAGE


class TemporalLink(BaseModel):
    namespace: str
    workflows_url: str
    redirect_endpoint: str


class TemporalWorkflowSummary(BaseModel):
    runbook_id: str
    title: str
    workflow_id: str
    status: str
    cadence: str
    retry_policy: str
    sla: str
    checkpoints: list[str]


class TemporalDetails(BaseModel):
    namespace: str
    status: str
    backend_address: str
    backend_connected: bool
    backend_error: str | None
    task_queue: str
    action_workflow_type: str
    approval_signal_name: str
    approval_stage: str
    workflows_url: str
    redirect_endpoint: str
    cors_origins: list[str]
    backend_endpoints: dict[str, str]
    workflow_count: int
    workflows: list[TemporalWorkflowSummary]


class RunbookActionResponse(BaseModel):
    runbook_id: str
    action: str
    status: str
    temporal_workflows_url: str
    temporal_workflow_id: str | None = None
    message: str


class HumanApprovalRequest(BaseModel):
    approver: str = "operator"
    approved: bool = True
    notes: str = ""
    stage: str = TEMPORAL_APPROVAL_STAGE


class HumanApprovalResponse(BaseModel):
    runbook_id: str
    status: str
    approval_signal_name: str | None = None
    temporal_workflows_url: str
    message: str


class TemporalBackendConnection(BaseModel):
    address: str
    namespace: str
    web_url: str
    sdk_installed: bool
    connected: bool
    tls_enabled: bool
    task_queue: str
    action_workflow_type: str
    approval_signal_name: str
    approval_stage: str
    error: str | None = None


class TriggerWorkflowRequest(BaseModel):
    signal_data: dict


class TriggerWorkflowResponse(BaseModel):
    workflow_id: str


class ShadowTestResult(BaseModel):
    status: str
    summary: str | None = None
    production_results: list = []
    candidate_results: list = []
    diff: list[str] = []
    error: str | None = None
