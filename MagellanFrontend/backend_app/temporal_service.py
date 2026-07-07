import asyncio
import importlib
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .config import (
    TEMPORAL_ACTION_WORKFLOW_TYPE,
    TEMPORAL_ADDRESS,
    TEMPORAL_APPROVAL_SIGNAL_NAME,
    TEMPORAL_APPROVAL_STAGE,
    TEMPORAL_CONNECTION_TIMEOUT_SECONDS,
    TEMPORAL_NAMESPACE,
    TEMPORAL_TASK_QUEUE,
    TEMPORAL_TLS_ENABLED,
    TEMPORAL_WORKFLOWS_URL,
)
from .normalizers import (
    normalize_audit_row,
    normalize_runbook,
    status_from_temporal_workflow,
)
from .state import APPROVAL_RECORDS


def parse_temporal_datetime(value: str) -> datetime | None:
    if not value or value == "None":
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def temporal_workflow_runtime_seconds(workflow: dict[str, str]) -> int:
    start_time = parse_temporal_datetime(workflow.get("start_time", ""))
    if start_time is None:
        return 1

    close_time = parse_temporal_datetime(workflow.get("close_time", ""))
    end_time = close_time or datetime.now(timezone.utc)
    return max(1, int((end_time - start_time).total_seconds()))


def temporal_status_metrics(status: str, runtime_seconds: int) -> dict[str, float | int]:
    normalized_status = status.upper()
    runtime_signal = min(max(runtime_seconds, 1), 999)

    if normalized_status == "COMPLETED":
        return {
            "queryVolume": 1,
            "exitRate": 0,
            "revenueLoss": 0,
            "baselineNdcg": 0.82,
            "proposedNdcg": 0.98,
            "p95Latency": runtime_signal,
            "businessImpact": 72,
            "offlineEvalCoverage": 100,
            "confidence": 98,
        }

    if normalized_status == "RUNNING":
        return {
            "queryVolume": 1,
            "exitRate": 12,
            "revenueLoss": 0,
            "baselineNdcg": 0.64,
            "proposedNdcg": 0.82,
            "p95Latency": runtime_signal,
            "businessImpact": 38,
            "offlineEvalCoverage": 60,
            "confidence": 82,
        }

    if normalized_status == "FAILED":
        return {
            "queryVolume": 1,
            "exitRate": 78,
            "revenueLoss": runtime_signal,
            "baselineNdcg": 0.24,
            "proposedNdcg": 0.4,
            "p95Latency": runtime_signal,
            "businessImpact": 90,
            "offlineEvalCoverage": 25,
            "confidence": 35,
        }

    return {
        "queryVolume": 1,
        "exitRate": 35,
        "revenueLoss": 0,
        "baselineNdcg": 0.5,
        "proposedNdcg": 0.65,
        "p95Latency": runtime_signal,
        "businessImpact": 50,
        "offlineEvalCoverage": 40,
        "confidence": 55,
    }


def approval_state_for_temporal_workflow(workflow: dict[str, str]) -> dict[str, str]:
    workflow_id = workflow.get("workflow_id") or "unknown-workflow"
    workflow_type = workflow.get("workflow_type") or "TemporalWorkflow"
    status = (workflow.get("status") or "UNKNOWN").upper()
    saved_approval = APPROVAL_RECORDS.get(workflow_id)

    if saved_approval:
        return {
            "mode": "required",
            "owner": str(saved_approval.get("approver") or "Temporal operator"),
            "status": "Approved" if saved_approval.get("approved") else "Rejected",
            "reason": "Human approval was recorded after the fixing agent generated the runbook.",
            "expiry": "Approval signal already submitted.",
            "record": str(saved_approval.get("record") or "Approval signal submitted to Temporal."),
        }

    if workflow_type in ("FullPipelineWorkflow", "UnifiedSearchAiRepairWorkflow") and status == "RUNNING":
        return {
            "mode": "required",
            "owner": "Search lead / Temporal operator",
            "status": "Pending",
            "reason": (
                "Fixing agents have generated the runbook. Temporal should wait here for "
                "human approval before apply-fix, feedback, and canary tasks continue."
            ),
            "expiry": "Required before downstream Temporal tasks continue.",
            "record": "Waiting for human approval signal at the post-fix-plan gate.",
        }

    return {
        "mode": "auto",
        "owner": "Temporal workflow",
        "status": "Completed" if status == "COMPLETED" else "Not required",
        "reason": "No active post-fix human approval gate is exposed for this workflow row.",
        "expiry": "Not applicable.",
        "record": "No pending approval signal required for this workflow.",
    }


def build_runbook_from_temporal_workflow(workflow: dict[str, str]) -> dict:
    workflow_id = workflow.get("workflow_id") or "unknown-workflow"
    workflow_type = workflow.get("workflow_type") or "TemporalWorkflow"
    status = workflow.get("status") or "UNKNOWN"
    task_queue = workflow.get("task_queue") or "not provided"
    run_id = workflow.get("run_id") or "not provided"
    runtime_seconds = temporal_workflow_runtime_seconds(workflow)
    status_metrics = temporal_status_metrics(status, runtime_seconds)
    approval_state = approval_state_for_temporal_workflow(workflow)

    return normalize_runbook(
        {
            "id": workflow_id,
            "title": f"{workflow_type} - {status}",
            "description": (
                f"Live Temporal workflow from backend service {TEMPORAL_ADDRESS}. "
                f"Run ID: {run_id}. Task queue: {task_queue}."
            ),
            "visualCode": "".join(part[:1] for part in workflow_type.split("_"))[:2].upper() or "TW",
            "capability": "semantic search",
            "signalType": "catalog gap",
            "risk": "high" if status.upper() == "FAILED" else "low",
            "confidence": status_metrics["confidence"],
            "tags": ["temporal-backend", workflow_type, status.lower()],
            "status": status_from_temporal_workflow(status),
            "offlineEvalCoverage": status_metrics["offlineEvalCoverage"],
            "businessImpact": status_metrics["businessImpact"],
            "rootCause": (
                "Temporal workflow list metadata does not expose activity output. "
                "The exact root cause must come from the backend runbook result source, "
                "for example RUNBOOKS_API_URL or a Temporal workflow query."
            ),
            "businessImpactSummary": (
                f"Metadata-derived impact score is {status_metrics['businessImpact']} for workflow status {status}. "
                "Exact business impact text must come from the impact activity output."
            ),
            "problemStatement": (
                f"Workflow {workflow_id} is currently {status}. "
                "FastAPI can show lifecycle state from Temporal, but the exact problem statement "
                "must be exposed by the runbook detail backend."
            ),
            "fixSummary": (
                "The fix plan is generated inside the Temporal pipeline after the fixing agents run. "
                "Expose that runbook result through RUNBOOKS_API_URL or a Temporal query to show exact fix details."
            ),
            "fixPlanSteps": [
                "Read live workflow metadata from Temporal.",
                "Wait for fixing agents to generate the runbook.",
                "Expose root cause, impact, and immediate_fix_plan from the backend runbook result source.",
                "Send human approval before downstream apply-fix, feedback, and canary tasks continue.",
            ],
            "approvalPolicy": "Temporal backend workflow record. No mock approval policy generated.",
            "evidenceNotes": (
                f"Workflow ID {workflow_id} is returned from Temporal service at {TEMPORAL_ADDRESS}. "
                f"Started at {workflow.get('start_time') or 'not provided'}."
            ),
            "agent": {
                "name": workflow_type,
                "role": "Temporal workflow execution record from backend service.",
                "autonomyLevel": "Reported by Temporal service.",
                "behaviors": [
                    f"Workflow status: {status}.",
                    f"Task queue: {task_queue}.",
                    f"Run ID: {run_id}.",
                ],
                "decisionRecord": (
                    "This record is derived from Temporal backend workflow metadata, "
                    "not from local mock data."
                ),
            },
            "temporal": {
                "workflowId": workflow_id,
                "cadence": f"Started at {workflow.get('start_time') or 'not provided'}",
                "retryPolicy": "Read from Temporal workflow metadata only; retry policy not exposed by list API.",
                "sla": f"Status: {status}",
                "checkpoints": [
                    f"Workflow type: {workflow_type}",
                    f"Task queue: {task_queue}",
                    f"Run ID: {run_id}",
                ],
            },
            "humanApproval": {
                "mode": approval_state["mode"],
                "owner": approval_state["owner"],
                "status": approval_state["status"],
                "reason": approval_state["reason"],
                "expiry": approval_state["expiry"],
                "record": approval_state["record"],
            },
            "monitoringSignals": [
                {
                    "label": "Runtime",
                    "value": f"{runtime_seconds}s",
                    "status": "watch" if runtime_seconds > 600 else "healthy",
                    "detail": "Runtime is derived from Temporal start and close timestamps.",
                },
                {
                    "label": "Temporal status",
                    "value": status,
                    "status": "blocked" if status.upper() == "FAILED" else "healthy",
                    "detail": f"Workflow status reported by Temporal service at {TEMPORAL_ADDRESS}.",
                },
                {
                    "label": "Task queue",
                    "value": task_queue,
                    "status": "healthy",
                    "detail": "Task queue returned by Temporal workflow listing.",
                },
            ],
            "feedbackLoop": "Refresh Backend Details or Temporal Web to inspect latest workflow state.",
            "liveMetrics": {
                "queryVolume": status_metrics["queryVolume"],
                "exitRate": status_metrics["exitRate"],
                "revenueLoss": status_metrics["revenueLoss"],
                "baselineNdcg": status_metrics["baselineNdcg"],
                "proposedNdcg": status_metrics["proposedNdcg"],
                "p95Latency": status_metrics["p95Latency"],
            },
            "beforeQuery": workflow_id,
            "beforeResults": [],
            "afterResults": [],
        }
    )


def build_audit_from_temporal_workflow(workflow: dict[str, str]) -> dict:
    workflow_id = workflow.get("workflow_id") or "unknown-workflow"
    status = workflow.get("status") or "UNKNOWN"
    workflow_type = workflow.get("workflow_type") or "TemporalWorkflow"

    return normalize_audit_row(
        {
            "time": workflow.get("start_time") or "not provided",
            "runbookId": workflow_id,
            "title": workflow_type,
            "action": f"Temporal workflow observed with status {status}",
            "approver": "temporal:service",
            "agentName": workflow_type,
            "agentBehavior": f"Task queue: {workflow.get('task_queue') or 'not provided'}",
            "temporalWorkflowId": workflow_id,
            "approvalGate": "No approval state returned by Temporal workflow list.",
            "monitoringSummary": f"Status: {status}; Run ID: {workflow.get('run_id') or 'not provided'}",
            "feedbackRecord": "Live Temporal backend record rendered in frontend.",
            "recordType": "rollback" if status.upper() == "FAILED" else "monitoring",
            "hash": workflow.get("run_id") or workflow_id,
            "isRollback": status.upper() == "FAILED",
        }
    )


def get_temporal_client_class() -> Any:
    try:
        temporal_client_module = importlib.import_module("temporalio.client")
    except ModuleNotFoundError:
        return None
    return temporal_client_module.Client


async def connect_temporal_client() -> Any:
    client_class = get_temporal_client_class()
    if client_class is None:
        raise RuntimeError(
            "temporalio package is not installed. Install backend dependencies with "
            "`python3 -m pip install -r requirements.txt`."
        )

    connect_options: dict[str, Any] = {"namespace": TEMPORAL_NAMESPACE}
    if TEMPORAL_TLS_ENABLED:
        connect_options["tls"] = True

    return await asyncio.wait_for(
        client_class.connect(TEMPORAL_ADDRESS, **connect_options),
        timeout=TEMPORAL_CONNECTION_TIMEOUT_SECONDS,
    )


async def inspect_temporal_backend() -> dict[str, Any]:
    sdk_installed = get_temporal_client_class() is not None
    base_status = {
        "address": TEMPORAL_ADDRESS,
        "namespace": TEMPORAL_NAMESPACE,
        "web_url": TEMPORAL_WORKFLOWS_URL,
        "sdk_installed": sdk_installed,
        "connected": False,
        "tls_enabled": TEMPORAL_TLS_ENABLED,
        "task_queue": TEMPORAL_TASK_QUEUE or "not configured",
        "action_workflow_type": TEMPORAL_ACTION_WORKFLOW_TYPE or "not configured",
        "approval_signal_name": TEMPORAL_APPROVAL_SIGNAL_NAME or "not configured",
        "approval_stage": TEMPORAL_APPROVAL_STAGE,
        "error": None,
    }

    if not sdk_installed:
        return {
            **base_status,
            "error": "temporalio package is not installed.",
        }

    try:
        await connect_temporal_client()
        return {
            **base_status,
            "connected": True,
        }
    except Exception as exc:
        return {
            **base_status,
            "error": str(exc),
        }


async def start_temporal_action_workflow(runbook_id: str, action: str) -> str:
    if not TEMPORAL_ACTION_WORKFLOW_TYPE or not TEMPORAL_TASK_QUEUE:
        return ""

    client = await connect_temporal_client()
    workflow_id = f"runbook-action-{runbook_id}-{action}-{uuid4().hex[:10]}"
    handle = await client.start_workflow(
        TEMPORAL_ACTION_WORKFLOW_TYPE,
        {
            "runbook_id": runbook_id,
            "action": action,
        },
        id=workflow_id,
        task_queue=TEMPORAL_TASK_QUEUE,
    )
    return str(getattr(handle, "id", workflow_id))


async def trigger_workflow(signal_data: dict) -> str:
    """Starts a new UnifiedSearchAiRepairWorkflow with the given signal data."""
    client = await connect_temporal_client()
    if not client:
        raise ConnectionError("Could not connect to Temporal server.")

    workflow_id = f"unified-search-repair-workflow-{uuid4()}"
    
    signal_data.setdefault("type", "catalog") 

    await client.start_workflow(
        "UnifiedSearchAiRepairWorkflow",
        signal_data,
        id=workflow_id,
        task_queue=TEMPORAL_TASK_QUEUE or "search-ai-task-queue",
    )
    return workflow_id


async def signal_temporal_human_approval(
    workflow_id: str,
    approval_payload: dict[str, Any],
) -> str:
    if not TEMPORAL_APPROVAL_SIGNAL_NAME:
        return ""

    client = await connect_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal(TEMPORAL_APPROVAL_SIGNAL_NAME, approval_payload)
    return TEMPORAL_APPROVAL_SIGNAL_NAME


def serialize_temporal_workflow(workflow: Any) -> dict[str, str]:
    status = getattr(workflow, "status", "")
    workflow_type = getattr(workflow, "workflow_type", "")
    start_time = getattr(workflow, "start_time", "")
    close_time = getattr(workflow, "close_time", "")

    return {
        "workflow_id": str(getattr(workflow, "id", "")),
        "run_id": str(getattr(workflow, "run_id", "")),
        "workflow_type": str(getattr(workflow_type, "name", workflow_type)),
        "status": str(getattr(status, "name", status)),
        "task_queue": str(getattr(workflow, "task_queue", "")),
        "start_time": str(start_time),
        "close_time": str(close_time),
    }


async def trigger_workflow(signal_data: dict) -> str:
    """Starts a new UnifiedSearchAiRepairWorkflow with the given signal data."""
    client = await connect_temporal_client()
    if not client:
        raise ConnectionError("Could not connect to Temporal server.")

    workflow_id = f"unified-search-repair-workflow-{uuid4()}"
    
    # You might want to get the workflow type from the signal or a parameter
    # For now, let's assume a default or get it from the signal
    signal_data.setdefault("type", "catalog") 

    # Assuming UnifiedSearchAiRepairWorkflow is the one to run.
    # The actual workflow class might need to be imported or referenced differently
    # depending on your project structure. For now, we'll use its name as a string.
    await client.start_workflow(
        "UnifiedSearchAiRepairWorkflow",
        signal_data,
        id=workflow_id,
        task_queue=TEMPORAL_TASK_QUEUE or "search-ai-task-queue",
    )
    return workflow_id


async def list_temporal_backend_workflows(limit: int = 25) -> list[dict[str, str]]:
    client = await connect_temporal_client()
    workflows: list[dict[str, str]] = []

    async for workflow in client.list_workflows():
        workflows.append(serialize_temporal_workflow(workflow))
        if len(workflows) >= limit:
            break

    return workflows


async def get_workflow_result(workflow_id: str, run_id: str | None = None) -> Any:
    """Gets the result of a specific workflow run."""
    client = await connect_temporal_client()
    handle = client.get_workflow_handle(workflow_id, run_id=run_id)
    try:
        # Using a timeout to prevent waiting forever on a running workflow
        return await asyncio.wait_for(handle.result(), timeout=5.0)
    except asyncio.TimeoutError:
        return {"status": "RUNNING", "error": "Workflow is still running."}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


async def get_workflow_result(workflow_id: str, run_id: str | None = None) -> Any:
    """Gets the result of a specific workflow run."""
    client = await connect_temporal_client()
    handle = client.get_workflow_handle(workflow_id, run_id=run_id)
    try:
        # Using a timeout to prevent waiting forever on a running workflow
        return await asyncio.wait_for(handle.result(), timeout=5.0)
    except asyncio.TimeoutError:
        return {"status": "RUNNING", "error": "Workflow is still running."}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}
