import os
import json
from pathlib import Path
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel


def load_env_file(env_path: str = ".env") -> None:
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()


FASTAPI_HOST = os.getenv("FASTAPI_HOST", "127.0.0.1")
FASTAPI_PORT = os.getenv("FASTAPI_PORT", "8000")
PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", f"http://{FASTAPI_HOST}:{FASTAPI_PORT}")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TEMPORAL_WORKFLOWS_URL = os.getenv(
    "TEMPORAL_WORKFLOWS_URL",
    "http://localhost:8233/namespaces/default/workflows",
)
BACKEND_REQUEST_TIMEOUT_SECONDS = float(os.getenv("BACKEND_REQUEST_TIMEOUT_SECONDS", "8"))

DATA_SOURCE_URLS = {
    "runbooks": os.getenv("RUNBOOKS_API_URL", "").strip(),
    "audit": os.getenv("AUDIT_API_URL", "").strip(),
    "query_clusters": os.getenv("QUERY_CLUSTERS_API_URL", "").strip(),
}

RUNBOOK_ACTION_API_URL = os.getenv("RUNBOOK_ACTION_API_URL", "").strip()
DATA_API_BEARER_TOKEN = os.getenv("DATA_API_BEARER_TOKEN", "").strip()

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

FRONTEND_ORIGIN_REGEX = os.getenv(
    "FRONTEND_ORIGIN_REGEX",
    r"http://(localhost|127\.0\.0\.1|0\.0\.0\.0):[0-9]+",
)


def request_headers(content_type: str | None = None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if content_type:
        headers["Content-Type"] = content_type
    if DATA_API_BEARER_TOKEN:
        headers["Authorization"] = f"Bearer {DATA_API_BEARER_TOKEN}"
    return headers


def extract_list_payload(payload: Any, keys: list[str]) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    return []


def fetch_remote_list(source_name: str, keys: list[str]) -> list[dict]:
    url = DATA_SOURCE_URLS.get(source_name, "")
    if not url:
        return []

    try:
        request = Request(url, headers=request_headers())
        with urlopen(request, timeout=BACKEND_REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{source_name} source returned HTTP {exc.code}: {url}",
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{source_name} source is not reachable or returned invalid JSON: {url}",
        ) from exc

    return extract_list_payload(payload, keys)


def data_source_status() -> dict[str, dict[str, str | bool]]:
    return {
        name: {
            "configured": bool(url),
            "url": url if url else "not configured",
        }
        for name, url in DATA_SOURCE_URLS.items()
    }


def get_runbook_value(runbook: dict, *keys: str, default: Any = "") -> Any:
    for key in keys:
        value: Any = runbook
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                value = None
                break
            value = value[part]
        if value not in (None, ""):
            return value
    return default


def number_value(value: Any, default: float = 0) -> float:
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except (TypeError, ValueError):
        return default


def int_value(value: Any, default: int = 0) -> int:
    return int(number_value(value, default))


def list_value(value: Any) -> list:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def allowed_value(value: Any, allowed: set[str], default: str) -> str:
    value_as_text = str(value).strip()
    return value_as_text if value_as_text in allowed else default


def normalize_search_results(value: Any) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def normalize_monitoring_signals(value: Any) -> list[dict]:
    if isinstance(value, list):
        signals = [item for item in value if isinstance(item, dict)]
    else:
        signals = []

    normalized = [
        {
            "label": str(signal.get("label") or signal.get("name") or "Monitoring signal"),
            "value": str(signal.get("value") or signal.get("metric") or "not provided"),
            "status": allowed_value(signal.get("status", "watch"), {"healthy", "watch", "blocked"}, "watch"),
            "detail": str(signal.get("detail") or signal.get("description") or "Provided by upstream source."),
        }
        for signal in signals
    ]

    while len(normalized) < 2:
        normalized.append(
            {
                "label": "Source data",
                "value": "configured",
                "status": "healthy",
                "detail": "Default monitoring placeholder because upstream did not provide two signals.",
            }
        )

    return normalized


def normalize_runbook(runbook: dict) -> dict:
    runbook_id = str(get_runbook_value(runbook, "id", "runbook_id", default="unknown"))
    title = str(get_runbook_value(runbook, "title", "name", default=runbook_id))
    agent = get_runbook_value(runbook, "agent", default={})
    temporal = get_runbook_value(runbook, "temporal", default={})
    human_approval = get_runbook_value(runbook, "humanApproval", "human_approval", default={})
    live_metrics = get_runbook_value(runbook, "liveMetrics", "live_metrics", "metrics", default={})

    if not isinstance(agent, dict):
        agent = {}
    if not isinstance(temporal, dict):
        temporal = {}
    if not isinstance(human_approval, dict):
        human_approval = {}
    if not isinstance(live_metrics, dict):
        live_metrics = {}

    return {
        "id": runbook_id,
        "title": title,
        "description": str(get_runbook_value(runbook, "description", "summary", default="No description provided.")),
        "visualCode": str(get_runbook_value(runbook, "visualCode", "visual_code", "code", default=runbook_id[:2].upper())),
        "capability": allowed_value(
            get_runbook_value(runbook, "capability", default="semantic search"),
            {"semantic search", "smart autocomplete", "merchandising"},
            "semantic search",
        ),
        "signalType": allowed_value(
            get_runbook_value(runbook, "signalType", "signal_type", default="catalog gap"),
            {"catalog gap", "zero-result cluster", "mxp rule conflict"},
            "catalog gap",
        ),
        "risk": allowed_value(get_runbook_value(runbook, "risk", "severity", default="low"), {"low", "med", "high"}, "low"),
        "confidence": int_value(get_runbook_value(runbook, "confidence", "score", default=0)),
        "tags": [str(tag) for tag in list_value(get_runbook_value(runbook, "tags", default=[]))],
        "status": allowed_value(
            get_runbook_value(runbook, "status", default="Eval Ready"),
            {
                "Eval Ready",
                "Shadow Test",
                "Canary 5%",
                "Canary 25%",
                "Canary 100%",
                "Owner Review",
                "Rollback Candidate",
                "Released",
                "Rolled Back",
            },
            "Eval Ready",
        ),
        "offlineEvalCoverage": int_value(get_runbook_value(runbook, "offlineEvalCoverage", "offline_eval_coverage", default=0)),
        "businessImpact": int_value(get_runbook_value(runbook, "businessImpact", "business_impact", "impact_score", default=0)),
        "approvalPolicy": str(get_runbook_value(runbook, "approvalPolicy", "approval_policy", default="Approval policy not provided.")),
        "evidenceNotes": str(get_runbook_value(runbook, "evidenceNotes", "evidence_notes", "evidence", default="No evidence notes provided.")),
        "agent": {
            "name": str(agent.get("name") or agent.get("agent_name") or "Pipeline Agent"),
            "role": str(agent.get("role") or "Provided by upstream pipeline."),
            "autonomyLevel": str(agent.get("autonomyLevel") or agent.get("autonomy_level") or "Not provided."),
            "behaviors": [str(item) for item in list_value(agent.get("behaviors") or ["No behavior details provided."])],
            "decisionRecord": str(agent.get("decisionRecord") or agent.get("decision_record") or "No decision record provided."),
        },
        "temporal": {
            "workflowId": str(
                temporal.get("workflowId")
                or temporal.get("workflow_id")
                or get_runbook_value(runbook, "workflow_id", "temporalWorkflowId", default=f"workflow/{runbook_id}")
            ),
            "cadence": str(temporal.get("cadence") or get_runbook_value(runbook, "cadence", default="not provided")),
            "retryPolicy": str(temporal.get("retryPolicy") or temporal.get("retry_policy") or get_runbook_value(runbook, "retry_policy", default="not provided")),
            "sla": str(temporal.get("sla") or get_runbook_value(runbook, "sla", default="not provided")),
            "checkpoints": [str(item) for item in list_value(temporal.get("checkpoints") or get_runbook_value(runbook, "checkpoints", default=[]))],
        },
        "humanApproval": {
            "mode": allowed_value(human_approval.get("mode", "conditional"), {"auto", "required", "conditional"}, "conditional"),
            "owner": str(human_approval.get("owner") or human_approval.get("approver") or "Not assigned"),
            "status": str(human_approval.get("status") or "Not requested"),
            "reason": str(human_approval.get("reason") or "No approval reason provided."),
            "expiry": str(human_approval.get("expiry") or "No expiry provided."),
            "record": str(human_approval.get("record") or "No approval record provided."),
        },
        "monitoringSignals": normalize_monitoring_signals(
            get_runbook_value(runbook, "monitoringSignals", "monitoring_signals", default=[])
        ),
        "feedbackLoop": str(get_runbook_value(runbook, "feedbackLoop", "feedback_loop", default="No feedback loop provided.")),
        "liveMetrics": {
            "queryVolume": int_value(live_metrics.get("queryVolume") or live_metrics.get("query_volume") or get_runbook_value(runbook, "query_volume", default=0)),
            "exitRate": number_value(live_metrics.get("exitRate") or live_metrics.get("exit_rate") or get_runbook_value(runbook, "exit_rate", default=0)),
            "revenueLoss": int_value(live_metrics.get("revenueLoss") or live_metrics.get("revenue_loss") or get_runbook_value(runbook, "revenue_loss", default=0)),
            "baselineNdcg": number_value(live_metrics.get("baselineNdcg") or live_metrics.get("baseline_ndcg") or get_runbook_value(runbook, "baseline_ndcg", default=0)),
            "proposedNdcg": number_value(live_metrics.get("proposedNdcg") or live_metrics.get("proposed_ndcg") or get_runbook_value(runbook, "proposed_ndcg", default=0)),
            "p95Latency": int_value(live_metrics.get("p95Latency") or live_metrics.get("p95_latency") or get_runbook_value(runbook, "p95_latency", default=0)),
        },
        "accent": str(get_runbook_value(runbook, "accent", default="#1F6B77")),
        "accentGlow": str(get_runbook_value(runbook, "accentGlow", "accent_glow", default="rgba(31,107,119,0.12)")),
        "accentBorder": str(get_runbook_value(runbook, "accentBorder", "accent_border", default="rgba(31,107,119,0.25)")),
        "beforeQuery": str(get_runbook_value(runbook, "beforeQuery", "before_query", "query", default="")),
        "beforeResults": normalize_search_results(get_runbook_value(runbook, "beforeResults", "before_results", default=[])),
        "afterResults": normalize_search_results(get_runbook_value(runbook, "afterResults", "after_results", default=[])),
    }


def normalize_audit_row(row: dict) -> dict:
    return {
        "time": str(row.get("time") or row.get("created_at") or "not provided"),
        "runbookId": str(row.get("runbookId") or row.get("runbook_id") or "unknown"),
        "title": str(row.get("title") or "Audit record"),
        "action": str(row.get("action") or row.get("event") or "not provided"),
        "approver": str(row.get("approver") or row.get("actor") or "not provided"),
        "agentName": str(row.get("agentName") or row.get("agent_name") or "not provided"),
        "agentBehavior": str(row.get("agentBehavior") or row.get("agent_behavior") or "not provided"),
        "temporalWorkflowId": str(row.get("temporalWorkflowId") or row.get("temporal_workflow_id") or row.get("workflow_id") or "not provided"),
        "approvalGate": str(row.get("approvalGate") or row.get("approval_gate") or "not provided"),
        "monitoringSummary": str(row.get("monitoringSummary") or row.get("monitoring_summary") or "not provided"),
        "feedbackRecord": str(row.get("feedbackRecord") or row.get("feedback_record") or "not provided"),
        "recordType": allowed_value(row.get("recordType") or row.get("record_type"), {"evaluation", "approval", "release", "rollback", "monitoring"}, "monitoring"),
        "hash": str(row.get("hash") or row.get("id") or "not provided"),
        "isRollback": bool(row.get("isRollback") or row.get("is_rollback") or False),
    }


def normalize_query_cluster(row: dict) -> dict:
    return {
        "query": str(row.get("query") or row.get("cluster") or "unknown"),
        "volume": str(row.get("volume") or row.get("monthly_volume") or "0"),
        "exits": str(row.get("exits") or row.get("exit_rate") or "0%"),
        "loss": str(row.get("loss") or row.get("revenue_loss") or "$0"),
        "impact": allowed_value(row.get("impact") or row.get("impact_rank"), {"High", "Med", "Low"}, "Low"),
        "tag": str(row.get("tag") or row.get("issue_type") or "Unclassified"),
        "badgeClass": allowed_value(row.get("badgeClass") or row.get("badge_class"), {"waterproof", "typo", "rules"}, "rules"),
        "status": str(row.get("status") or "not triaged"),
    }


def build_workflow_summary(runbook: dict) -> "TemporalWorkflowSummary":
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
    message: str


app = FastAPI(
    title="Magellan AI Search Ops Backend",
    version="1.0.0",
    description="Backend bridge for the React dashboard and Temporal workflow UI.",
)

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
            "temporal_workflows_redirect": "/api/temporal/workflows",
            "runbook_action": "/api/runbooks/{runbook_id}/actions/{action}",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "backend_base_url": PUBLIC_BACKEND_URL,
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
def get_temporal_details() -> TemporalDetails:
    workflows = [build_workflow_summary(runbook) for runbook in get_runbooks()]

    return TemporalDetails(
        namespace=TEMPORAL_NAMESPACE,
        status="configured" if DATA_SOURCE_URLS["runbooks"] else "runbook source not configured",
        workflows_url=TEMPORAL_WORKFLOWS_URL,
        redirect_endpoint="/api/temporal/workflows",
        cors_origins=FRONTEND_ORIGINS,
        backend_endpoints={
            "runbooks": "/api/runbooks",
            "audit": "/api/audit",
            "query_clusters": "/api/query-clusters",
            "actions": "/api/runbooks/{runbook_id}/actions/{action}",
        },
        workflow_count=len(workflows),
        workflows=workflows,
    )


@app.get("/api/temporal/workflows")
def open_temporal_workflows() -> RedirectResponse:
    return RedirectResponse(TEMPORAL_WORKFLOWS_URL, status_code=307)


@app.get("/api/data-sources")
def get_data_sources() -> dict[str, dict[str, str | bool]]:
    return data_source_status()


@app.get("/api/runbooks")
def get_runbooks() -> list[dict]:
    return [
        normalize_runbook(runbook)
        for runbook in fetch_remote_list("runbooks", ["runbooks", "items", "data", "results"])
    ]


@app.get("/api/audit")
def get_audit() -> list[dict]:
    return [
        normalize_audit_row(row)
        for row in fetch_remote_list("audit", ["audit", "audit_rows", "items", "data", "results"])
    ]


@app.get("/api/query-clusters")
def get_query_clusters() -> list[dict]:
    return [
        normalize_query_cluster(row)
        for row in fetch_remote_list("query_clusters", ["query_clusters", "clusters", "items", "data", "results"])
    ]


@app.post("/api/runbooks/{runbook_id}/actions/{action}", response_model=RunbookActionResponse)
def run_runbook_action(
    runbook_id: str,
    action: Literal["evaluate", "release", "rollback"],
) -> RunbookActionResponse:
    forwarded = forward_runbook_action(runbook_id, action)

    return RunbookActionResponse(
        runbook_id=runbook_id,
        action=action,
        status="forwarded" if forwarded else "not_configured",
        temporal_workflows_url=TEMPORAL_WORKFLOWS_URL,
        message=(
            "Action was forwarded to the configured RUNBOOK_ACTION_API_URL."
            if forwarded
            else "No RUNBOOK_ACTION_API_URL configured. FastAPI did not execute a mock mutation."
        ),
    )
