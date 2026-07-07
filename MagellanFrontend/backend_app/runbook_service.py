import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException

from .config import (
    BACKEND_REQUEST_TIMEOUT_SECONDS,
    DATA_SOURCE_URLS,
    RUNBOOK_ACTION_API_URL,
)
from .data_sources import fetch_remote_list, request_headers
from .normalizers import (
    get_runbook_value,
    normalize_audit_row,
    normalize_runbook,
)
from .schemas import TemporalWorkflowSummary
from .temporal_service import (
    build_audit_from_temporal_workflow,
    build_runbook_from_temporal_workflow,
    get_workflow_result,
    list_temporal_backend_workflows,
)


async def get_runbook_records() -> list[dict]:
    if DATA_SOURCE_URLS["runbooks"]:
        runbooks = [
            normalize_runbook(runbook)
            for runbook in fetch_remote_list("runbooks", ["runbooks", "items", "data", "results"])
        ]
    else:
        runbooks = []
        local_file = Path(__file__).parent.parent / "data" / "runbooks.json"
        if local_file.exists():
            try:
                with open(local_file, "r") as f:
                    local_data = json.load(f)
                    if isinstance(local_data, list):
                        runbooks.extend([normalize_runbook(rb) for rb in local_data])
            except Exception:
                pass

        try:
            temporal_runbooks = [
                build_runbook_from_temporal_workflow(workflow)
                for workflow in await list_temporal_backend_workflows()
            ]
            runbooks.extend(temporal_runbooks)
        except Exception:
            pass

    for runbook in runbooks:
        # Only query result for completed/released workflows to avoid blocking the API
        if runbook.get("temporal", {}).get("workflowId") and runbook.get("status") not in ["Shadow Test", "RUNNING", "Pending"]:
            try:
                shadow_test_result = await get_workflow_result(runbook["temporal"]["workflowId"])
                if shadow_test_result:
                    runbook["shadowTest"] = shadow_test_result
            except Exception:
                pass  # It's okay if a shadow test result doesn't exist

    return runbooks


async def get_audit_records() -> list[dict]:
    if DATA_SOURCE_URLS["audit"]:
        return [
            normalize_audit_row(row)
            for row in fetch_remote_list("audit", ["audit", "audit_rows", "items", "data", "results"])
        ]

    audit_rows = []
    local_file = Path(__file__).parent.parent / "data" / "audit.json"
    if local_file.exists():
        try:
            with open(local_file, "r") as f:
                local_data = json.load(f)
                if isinstance(local_data, list):
                    audit_rows.extend([normalize_audit_row(row) for row in local_data])
        except Exception:
            pass

    try:
        temporal_audit = [
            build_audit_from_temporal_workflow(workflow)
            for workflow in await list_temporal_backend_workflows()
        ]
        audit_rows.extend(temporal_audit)
    except Exception:
        pass

    return audit_rows


def build_workflow_summary(runbook: dict) -> TemporalWorkflowSummary:
    runbook_id = str(get_runbook_value(runbook, "id", "runbook_id", default="unknown"))
    checkpoints = get_runbook_value(
        runbook,
        "temporal.checkpoints",
        "checkpoints",
        default=[],
    )
    if not isinstance(checkpoints, list):
        checkpoints = [str(checkpoints)] if checkpoints else []

    return TemporalWorkflowSummary(
        runbook_id=runbook_id,
        title=str(get_runbook_value(runbook, "title", "name", default=runbook_id)),
        workflow_id=str(
            get_runbook_value(
                runbook,
                "temporal.workflowId",
                "workflow_id",
                "temporalWorkflowId",
                default=f"workflow/{runbook_id}",
            )
        ),
        status=str(get_runbook_value(runbook, "status", default="unknown")),
        cadence=str(get_runbook_value(runbook, "temporal.cadence", "cadence", default="not provided")),
        retry_policy=str(
            get_runbook_value(runbook, "temporal.retryPolicy", "retry_policy", default="not provided")
        ),
        sla=str(get_runbook_value(runbook, "temporal.sla", "sla", default="not provided")),
        checkpoints=[str(checkpoint) for checkpoint in checkpoints],
    )


def build_action_url(runbook_id: str, action: str) -> str:
    if not RUNBOOK_ACTION_API_URL:
        return ""
    if "{runbook_id}" in RUNBOOK_ACTION_API_URL or "{action}" in RUNBOOK_ACTION_API_URL:
        return RUNBOOK_ACTION_API_URL.format(runbook_id=runbook_id, action=action)
    return f"{RUNBOOK_ACTION_API_URL.rstrip('/')}/{runbook_id}/actions/{action}"


def forward_runbook_action(runbook_id: str, action: str) -> bool:
    action_url = build_action_url(runbook_id, action)
    if not action_url:
        return False

    body = json.dumps({"runbook_id": runbook_id, "action": action}).encode("utf-8")
    try:
        request = Request(
            action_url,
            data=body,
            headers=request_headers("application/json"),
            method="POST",
        )
        with urlopen(request, timeout=BACKEND_REQUEST_TIMEOUT_SECONDS):
            return True
    except HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"runbook action source returned HTTP {exc.code}: {action_url}",
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"runbook action source is not reachable: {action_url}",
        ) from exc

async def update_runbook_from_workflow(workflow_id: str, result: dict) -> dict:
    """
    Finds a runbook by its workflow_id and updates it with the final
    results from a completed Temporal workflow run.
    """
    # This is a mock implementation. In a real application, you would
    # be updating a record in a database.
    runbooks = await get_runbook_records()
    for runbook in runbooks:
        if get_runbook_value(runbook, "temporal.workflowId", "workflow_id") == workflow_id:
            # We found the matching runbook, now update it.
            runbook["status"] = "Completed"
            runbook["final_result"] = result
            # Here you would save the updated runbook to your database.
            return runbook
    
    raise HTTPException(status_code=404, detail=f"Runbook with workflow_id '{workflow_id}' not found.")
