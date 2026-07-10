import json
from pathlib import Path
from typing import Literal
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from .config import (
    FRONTEND_ORIGIN_REGEX,
    FRONTEND_ORIGINS,
    PUBLIC_BACKEND_URL,
    TEMPORAL_ADDRESS,
    TEMPORAL_NAMESPACE,
    TEMPORAL_WORKFLOWS_URL,
    TEMPORAL_APPROVAL_SIGNAL_NAME,
    TEMPORAL_APPROVAL_STAGE,
)
from .data_sources import data_source_status, fetch_remote_list
from .normalizers import normalize_query_cluster
from .runbook_service import (
    build_workflow_summary,
    forward_runbook_action,
    get_audit_records,
    get_runbook_records,
    update_runbook_from_workflow,
)
from .schemas import (
    HumanApprovalRequest,
    HumanApprovalResponse,
    RunbookActionResponse,
    TemporalBackendConnection,
    TemporalDetails,
    TemporalLink,
    TemporalLiveWorkflow,
    TriggerWorkflowRequest,
    TriggerWorkflowResponse,
    ShadowTestResult,
    WorkflowCompletionRequest,
)
from .state import APPROVAL_RECORDS
from .activity_store import init_db, save_activity, get_activities_for_workflow
from .mlflow_store import log_activity_to_mlflow
from .mlflow_store import log_workflow_to_mlflow
from .temporal_service import (
    get_workflow_result,
    inspect_temporal_backend,
    list_temporal_backend_workflows,
    signal_temporal_human_approval,
    start_temporal_action_workflow,
    trigger_workflow,
)


app = FastAPI(
    title="Magellan AI Search Ops Backend",
    version="1.0.0",
    description="Backend bridge for the React dashboard and Temporal workflow UI.",
)

# Initialize activity DB on startup
try:
    init_db()
except Exception:
    # If DB init fails, continue; endpoints will raise on use
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_origin_regex=FRONTEND_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {
        "service": "Magellan AI Search Ops Backend",
        "status": "ok",
        "docs": "/docs",
        "backend_base_url": PUBLIC_BACKEND_URL,
        "temporal_backend_address": TEMPORAL_ADDRESS,
        "temporal_workflows_url": TEMPORAL_WORKFLOWS_URL,
        "data_sources": data_source_status(),
        "endpoints": {
            "health": "/health",
            "runbooks": "/api/runbooks",
            "audit": "/api/audit",
            "query_clusters": "/api/query-clusters",
            "data_sources": "/api/data-sources",
            "temporal": "/api/temporal",
            "temporal_details": "/api/temporal/details",
            "temporal_backend": "/api/temporal/backend",
            "temporal_live_workflows": "/api/temporal/live-workflows",
            "temporal_workflows_redirect": "/api/temporal/workflows",
            "human_approval": "/api/runbooks/{runbook_id}/approval",
            "runbook_action": "/api/runbooks/{runbook_id}/actions/{action}",
            "runbook_complete": "/api/runbooks/complete-run",
        },
    }

@app.get("/api/shadow-reports")
async def get_all_shadow_reports() -> list[dict]:
    """
    Scans the evaluation output directory, reads all shadow test report
    JSON files, and returns them as a single aggregated list.
    """
    reports = []
    # Assumes the backend is run from the `MagellanFrontend` directory
    output_dir = Path(__file__).parent.parent.parent / "evaluation/output"
    if not output_dir.exists():
        return []

    for report_file in sorted(output_dir.glob("eval_*.json"), reverse=True):
        try:
            with open(report_file, "r") as f:
                report_data = json.load(f)
                # Ensure the report has a workflow_id for the frontend key
                if 'workflow_id' not in report_data:
                    report_data['workflow_id'] = report_file.stem.replace('eval_', '')
                reports.append(report_data)
        except (json.JSONDecodeError, IOError):
            # Ignore files that are corrupted or cannot be read
            pass
    
    return reports

@app.post("/api/temporal/trigger-workflow", response_model=TriggerWorkflowResponse)
async def trigger_new_workflow(request: TriggerWorkflowRequest) -> TriggerWorkflowResponse:
    try:
        workflow_id = await trigger_workflow(request.signal_data)
        return TriggerWorkflowResponse(workflow_id=workflow_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/runbooks/complete-run")
async def complete_runbook_run(request: WorkflowCompletionRequest) -> dict:
    try:
        updated_runbook = await update_runbook_from_workflow(request.workflow_id, request.result)
        return {"status": "success", "updated_runbook": updated_runbook}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/temporal/activity-result")
async def ingest_activity_result(payload: dict) -> dict:
    """
    Ingests a single activity result for a workflow. Expected payload:
    {
      "workflow_id": "<workflow_id>",
      "activity_id": "<activity_id>",
      "activity_name": "<friendly name>",
      "result": { ... arbitrary payload ... }
    }
    """
    workflow_id = payload.get("workflow_id")
    if not workflow_id:
        raise HTTPException(status_code=400, detail="Missing workflow_id")

    received_at = datetime.utcnow().isoformat() + "Z"
    activity_id = payload.get("activity_id") or payload.get("activity_name") or "unknown-activity"
    activity_name = payload.get("activity_name") or payload.get("activity_id") or "activity"
    result = payload.get("result") or {}

    try:
        saved = save_activity(workflow_id, activity_id, activity_name, result, received_at)
        # Also log activity-level details to MLflow (best-effort)
        try:
            log_activity_to_mlflow({
                "workflow_id": workflow_id,
                "activity_id": activity_id,
                "activity_name": activity_name,
                "result": result,
                "received_at": received_at,
            })
        except Exception:
            # Don't fail the API if MLflow logging fails; it's best-effort telemetry
            pass
        return {"status": "ok", "workflow_id": workflow_id, "activity": saved}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))



@app.post("/api/temporal/workflow-result")
async def ingest_workflow_result(payload: dict) -> dict:
    """
    Ingests a full workflow-level result/summary and logs it to MLflow.
    Expected payload:
    {
      "workflow_id": "<workflow_id>",
      "result": { ... }
    }
    """
    workflow_id = payload.get("workflow_id")
    if not workflow_id:
        raise HTTPException(status_code=400, detail="Missing workflow_id")

    summary = payload.get("result") or payload.get("summary") or {}
    try:
        # best-effort MLflow logging
        try:
            info = log_workflow_to_mlflow(workflow_id, summary)
        except Exception:
            info = {"workflow_run_id": None}

        return {"status": "ok", "workflow_id": workflow_id, "mlflow": info}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/temporal/activities/{workflow_id}")
async def get_activity_results(workflow_id: str) -> list[dict]:
    """Returns all recorded activity-level results for a given workflow_id."""
    try:
        return get_activities_for_workflow(workflow_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/shadow-test/{workflow_id}", response_model=ShadowTestResult)
async def get_shadow_test_report(workflow_id: str) -> ShadowTestResult:
    try:
        result = await get_workflow_result(workflow_id)
        if not result:
            raise HTTPException(status_code=404, detail="Workflow result not found.")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "backend_base_url": PUBLIC_BACKEND_URL,
        "temporal_backend_address": TEMPORAL_ADDRESS,
        "temporal_workflows_url": TEMPORAL_WORKFLOWS_URL,
        "data_sources_configured": str(
            sum(1 for source in data_source_status().values() if source["configured"])
        ),
    }


@app.get("/api/temporal", response_model=TemporalLink)
def get_temporal_link() -> TemporalLink:
    return TemporalLink(
        namespace=TEMPORAL_NAMESPACE,
        workflows_url=TEMPORAL_WORKFLOWS_URL,
        redirect_endpoint="/api/temporal/workflows",
    )


@app.get("/api/temporal/details", response_model=TemporalDetails)
async def get_temporal_details() -> TemporalDetails:
    workflows = [build_workflow_summary(runbook) for runbook in await get_runbook_records()]
    temporal_backend = await inspect_temporal_backend()

    return TemporalDetails(
        namespace=TEMPORAL_NAMESPACE,
        status="connected" if temporal_backend["connected"] else "temporal backend not connected",
        backend_address=TEMPORAL_ADDRESS,
        backend_connected=temporal_backend["connected"],
        backend_error=temporal_backend["error"],
        task_queue=temporal_backend["task_queue"],
        action_workflow_type=temporal_backend["action_workflow_type"],
        approval_signal_name=TEMPORAL_APPROVAL_SIGNAL_NAME,
        approval_stage=TEMPORAL_APPROVAL_STAGE,
        workflows_url=TEMPORAL_WORKFLOWS_URL,
        redirect_endpoint="/api/temporal/workflows",
        cors_origins=FRONTEND_ORIGINS,
        backend_endpoints={
            "runbooks": "/api/runbooks",
            "audit": "/api/audit",
            "query_clusters": "/api/query-clusters",
            "human_approval": "/api/runbooks/{runbook_id}/approval",
            "actions": "/api/runbooks/{runbook_id}/actions/{action}",
        },
        workflow_count=len(workflows),
        workflows=workflows,
    )


@app.get("/api/temporal/workflows")
def open_temporal_workflows() -> RedirectResponse:
    return RedirectResponse(TEMPORAL_WORKFLOWS_URL, status_code=307)


@app.get("/api/temporal/backend", response_model=TemporalBackendConnection)
async def get_temporal_backend() -> TemporalBackendConnection:
    return TemporalBackendConnection(**await inspect_temporal_backend())


@app.get("/api/temporal/live-workflows")
async def get_temporal_live_workflows() -> list[dict[str, str]]:
    try:
        return await list_temporal_backend_workflows()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Temporal backend workflow list failed: {exc}",
        ) from exc


@app.post("/api/v1/workflows/trigger", response_model=TriggerWorkflowResponse)
async def trigger_agent_workflow(req: TriggerWorkflowRequest):
    """
    Triggers a new agent workflow.
    """
    try:
        workflow_id = await trigger_workflow(req.workflow_name, req.workflow_input)
        return TriggerWorkflowResponse(
            status="success",
            workflow_id=workflow_id,
            message=f"Workflow '{req.workflow_name}' started successfully.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflows", response_model=list[TemporalLiveWorkflow])
async def list_agent_workflows():
    """
    Lists all workflows.
    """
    try:
        return await list_temporal_backend_workflows()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/workflows/approval", response_model=HumanApprovalResponse)
async def human_approval_signal(req: HumanApprovalRequest):
    """
    Sends a human approval signal to a workflow.
    """
    try:
        await signal_temporal_human_approval(req.workflow_id, req.approval_status)
        return HumanApprovalResponse(
            status="success", message="Approval signal sent successfully."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data-sources")
def get_data_sources() -> dict[str, dict[str, str | bool]]:
    return data_source_status()


@app.get("/api/runbooks")
async def get_runbooks() -> list[dict]:
    return await get_runbook_records()


@app.get("/api/audit")
async def get_audit() -> list[dict]:
    return await get_audit_records()


@app.get("/api/query-clusters")
def get_query_clusters() -> list[dict]:
    results = fetch_remote_list("query_clusters", ["query_clusters", "clusters", "items", "data", "results"])
    if not results:
        local_file = Path(__file__).parent.parent / "data" / "query_clusters.json"
        if local_file.exists():
            try:
                with open(local_file, "r") as f:
                    results = json.load(f)
            except Exception:
                pass
    return [normalize_query_cluster(row) for row in results]


@app.post("/api/runbooks/{runbook_id}/approval", response_model=HumanApprovalResponse)
async def record_human_approval(
    runbook_id: str,
    approval: HumanApprovalRequest,
) -> HumanApprovalResponse:
    approval_record = {
        "runbook_id": runbook_id,
        "approved": approval.approved,
        "approver": approval.approver,
        "notes": approval.notes,
        "stage": approval.stage,
        "record": (
            f"{'Approved' if approval.approved else 'Rejected'} by {approval.approver} "
            f"at stage {approval.stage}."
        ),
    }
    APPROVAL_RECORDS[runbook_id] = approval_record

    signal_name = ""
    if approval.approved:
        try:
            signal_name = await signal_temporal_human_approval(runbook_id, approval_record)
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Human approval was recorded, but Temporal signal failed: {exc}",
            ) from exc

    return HumanApprovalResponse(
        runbook_id=runbook_id,
        status="signaled" if signal_name else "rejected" if not approval.approved else "recorded",
        approval_signal_name=signal_name or None,
        temporal_workflows_url=TEMPORAL_WORKFLOWS_URL,
        message=(
            f"Human approval recorded and Temporal signal `{signal_name}` sent. "
            "The workflow can continue with downstream apply-fix, feedback, and canary tasks."
            if signal_name
            else "Human rejection recorded. No Temporal continue signal was sent."
            if not approval.approved
            else "Human approval recorded locally. No Temporal approval signal name is configured."
        ),
    )


@app.post("/api/runbooks/{runbook_id}/actions/{action}", response_model=RunbookActionResponse)
async def run_runbook_action(
    runbook_id: str,
    action: Literal["evaluate", "release", "rollback"],
) -> RunbookActionResponse:
    forwarded = forward_runbook_action(runbook_id, action)
    temporal_workflow_id = ""
    if not forwarded:
        temporal_workflow_id = await start_temporal_action_workflow(runbook_id, action)

    return RunbookActionResponse(
        runbook_id=runbook_id,
        action=action,
        status="forwarded" if forwarded else "temporal_started" if temporal_workflow_id else "not_configured",
        temporal_workflows_url=TEMPORAL_WORKFLOWS_URL,
        temporal_workflow_id=temporal_workflow_id or None,
        message=(
            "Action was forwarded to the configured RUNBOOK_ACTION_API_URL."
            if forwarded
            else f"Temporal workflow started with id {temporal_workflow_id}."
            if temporal_workflow_id
            else (
                "No RUNBOOK_ACTION_API_URL or Temporal action workflow is configured. "
                "FastAPI did not execute a mock mutation."
            )
        ),
    )
