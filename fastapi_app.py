import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
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


TEMPORAL_WORKFLOWS_URL = os.getenv(
    "TEMPORAL_WORKFLOWS_URL",
    "http://localhost:8233/namespaces/default/workflows",
)

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


RUNBOOKS = [
    {
        "id": "ops-4f72",
        "title": 'Catalog Enrichment — "Waterproof" Attribute Gap',
        "description": 'AI Search fails to surface waterproof trail shoes because the catalog lacks a structured "waterproof" attribute. Embedding drift compounds missed synonym expansions.',
        "visualCode": "CE",
        "capability": "semantic search",
        "signalType": "catalog gap",
        "risk": "high",
        "confidence": 91,
        "tags": ["catalog-enrichment-qa", "semantic-search"],
        "status": "Eval Ready",
        "offlineEvalCoverage": 91,
        "businessImpact": 78,
        "approvalPolicy": "Auto-approve if NDCG ≥ 0.84",
        "evidenceNotes": 'Magellan detects 18% search-exit rate on the query cluster "waterproof trail shoes." Root cause: missing structured attribute in product taxonomy. AI suggests adding a boolean waterproof facet and re-indexing the vector store.',
        "agent": {
            "name": "Catalog Optimization Agent",
            "role": "Diagnoses missing catalog attributes and proposes index-safe enrichment patches.",
            "autonomyLevel": "Autonomous evaluation and canary release when all policy gates pass.",
            "behaviors": [
                "Clusters failed queries against product taxonomy gaps.",
                "Generates facet and synonym patch candidates with bounded schema changes.",
                "Blocks release when NDCG, latency, or inventory coverage gates fail.",
            ],
            "decisionRecord": "Stores structured rationale, evidence IDs, policy checks, and recommendation outcome. Private chain-of-thought is not stored.",
        },
        "temporal": {
            "workflowId": "temporal/catalog-gap/ops-4f72",
            "cadence": "Triggered when exit-rate cluster exceeds 1,000 failed sessions/day.",
            "retryPolicy": "Retry enrichment, eval, and shadow tasks up to 3 times with exponential backoff.",
            "sla": "30 minute eval SLA; page owner only if quality or latency gates fail.",
            "checkpoints": [
                "Evidence capture",
                "Schema patch draft",
                "Offline relevance eval",
                "Shadow traffic replay",
                "Canary telemetry monitor",
            ],
        },
        "humanApproval": {
            "mode": "auto",
            "owner": "Search relevance lead on exception",
            "status": "Not required",
            "reason": "Policy allows automation when NDCG >= floor and monitoring checks stay healthy.",
            "expiry": "Exception review within 4 business hours if triggered.",
            "record": "No human approval requested unless an eval or canary guardrail fails.",
        },
        "monitoringSignals": [
            {"label": "NDCG delta", "value": "+0.31", "status": "healthy", "detail": "Expected relevance lift clears policy floor."},
            {"label": "P95 latency", "value": "118ms", "status": "healthy", "detail": "Below global 150ms ceiling."},
            {"label": "Zero-result exits", "value": "-18%", "status": "watch", "detail": "Watched during canary for waterproof query cluster."},
        ],
        "feedbackLoop": "Post-release clicks, add-to-cart rate, and exit deltas are fed back into the taxonomy gap detector for 7-day drift review.",
        "liveMetrics": {
            "queryVolume": 12800,
            "exitRate": 18,
            "revenueLoss": 4200,
            "baselineNdcg": 0.6,
            "proposedNdcg": 0.91,
            "p95Latency": 118,
        },
        "accent": "#8B3A2B",
        "accentGlow": "rgba(139,58,43,0.12)",
        "accentBorder": "rgba(139,58,43,0.25)",
        "beforeQuery": "waterproof trail shoes",
        "beforeResults": [
            {"name": "Trail Runner X1", "price": 89, "stock": 4, "score": "0.41"},
            {"name": "Summer Sandal Pro", "price": 32, "stock": 18, "score": "0.38"},
            {"name": "Office Loafer Classic", "price": 65, "stock": 11, "score": "0.22"},
        ],
        "afterResults": [
            {"name": "AquaShield GTX Boot", "price": 149, "stock": 22, "score": "0.94"},
            {"name": "StormProof Trail Pro", "price": 119, "stock": 15, "score": "0.91"},
            {"name": "RainGuard Hiker", "price": 99, "stock": 8, "score": "0.88"},
        ],
    },
    {
        "id": "ops-1a88",
        "title": 'Autocomplete Exits — "Hydration Pack" Typo Cluster',
        "description": 'Smart autocomplete fails on user typos like "hydra p" and "hydra pack". The synonym graph lacks phonetic fuzzy matches for hydration-related queries.',
        "visualCode": "AC",
        "capability": "smart autocomplete",
        "signalType": "zero-result cluster",
        "risk": "med",
        "confidence": 86,
        "tags": ["autocomplete-tuning", "synonym-gap"],
        "status": "Eval Ready",
        "offlineEvalCoverage": 86,
        "businessImpact": 62,
        "approvalPolicy": "Auto-approve if NDCG ≥ 0.84",
        "evidenceNotes": 'Magellan clusters 5,400 monthly queries around "hydra p / hydra pack" with a 32% exit rate. No synonym mapping exists for these typos. Autocomplete Agent recommends phonetic fuzzy-match rules.',
        "agent": {
            "name": "Smart Autocomplete Agent",
            "role": "Finds failed prefixes, typo clusters, and missing synonym expansions.",
            "autonomyLevel": "Autonomous rule proposal with conditional approval for high-volume prefix rewrites.",
            "behaviors": [
                "Compares prefix failures with successful downstream product clicks.",
                "Builds phonetic and slang synonym candidates with rollback-safe rule IDs.",
                "Escalates if a rewrite affects protected brand or compliance terms.",
            ],
            "decisionRecord": "Stores detected prefix cluster, generated rule IDs, confidence score, and release decision. Private chain-of-thought is not stored.",
        },
        "temporal": {
            "workflowId": "temporal/autocomplete-tuning/ops-1a88",
            "cadence": "Runs hourly against failed-prefix logs and queued zero-result clusters.",
            "retryPolicy": "Retry prefix replay and latency tests twice; hold queue after repeated misses.",
            "sla": "15 minute tuning SLA; route to owner if affected query volume crosses 10k/month.",
            "checkpoints": [
                "Prefix cluster intake",
                "Synonym candidate generation",
                "Offline replay",
                "Shadow suggest API",
                "Canary conversion monitor",
            ],
        },
        "humanApproval": {
            "mode": "conditional",
            "owner": "Search experience owner",
            "status": "Not required",
            "reason": "Automation allowed unless protected terms or excessive rewrite scope are detected.",
            "expiry": "Conditional review due within 2 business hours if triggered.",
            "record": "Approval-not-needed record is saved when protected-term checks pass.",
        },
        "monitoringSignals": [
            {"label": "Prefix recall", "value": "+42%", "status": "healthy", "detail": "Hydration pack variants now map to expected product family."},
            {"label": "Suggest latency", "value": "91ms", "status": "healthy", "detail": "Autocomplete stays under latency ceiling."},
            {"label": "Rewrite scope", "value": "3 rules", "status": "watch", "detail": "Limited rollout monitors accidental broad matches."},
        ],
        "feedbackLoop": "Accepted suggestions, abandoned prefixes, and downstream conversion deltas update the typo-cluster model after each canary window.",
        "liveMetrics": {
            "queryVolume": 5400,
            "exitRate": 32,
            "revenueLoss": 2100,
            "baselineNdcg": 0.54,
            "proposedNdcg": 0.86,
            "p95Latency": 91,
        },
        "accent": "#1F6B77",
        "accentGlow": "rgba(31,107,119,0.12)",
        "accentBorder": "rgba(31,107,119,0.25)",
        "beforeQuery": "hydra pack",
        "beforeResults": [
            {"name": "Hydra Skin Cream", "price": 12, "stock": 40, "score": "0.30"},
            {"name": "Dragon Action Figure", "price": 19, "stock": 7, "score": "0.18"},
        ],
        "afterResults": [
            {"name": "CamelBak Hydration Pack 3L", "price": 79, "stock": 34, "score": "0.96"},
            {"name": "Osprey Hydration Reservoir", "price": 45, "stock": 18, "score": "0.92"},
            {"name": "TrailSip Hydra-Pack 2L", "price": 39, "stock": 22, "score": "0.89"},
        ],
    },
    {
        "id": "ops-7b19",
        "title": "MXP Merchandising Rule Conflict — Winter Clearance",
        "description": 'A manual merchandising boost for "winter jacket clearance" is pinning stale clearance inventory above higher-converting new arrivals. Conversion rate drops 14%.',
        "visualCode": "MX",
        "capability": "merchandising",
        "signalType": "mxp rule conflict",
        "risk": "high",
        "confidence": 88,
        "tags": ["mxp-rule-governance", "merchandising"],
        "status": "Owner Review",
        "offlineEvalCoverage": 88,
        "businessImpact": 85,
        "approvalPolicy": "Requires search lead manual sign-off",
        "evidenceNotes": "Magellan detects a manual boost rule pinning out-of-season clearance stock in position 1-3, overriding the ML relevance model. Exit rate is 14% while top competitor pages convert at 6%.",
        "agent": {
            "name": "Merchandising Rules Agent",
            "role": "Detects conflicts between manual boosts, inventory health, and relevance models.",
            "autonomyLevel": "Recommend-only until a human search lead signs the override change.",
            "behaviors": [
                "Compares pinned inventory against conversion, stock, seasonality, and relevance score.",
                "Suggests boost demotion or expiry changes with rollback snapshots.",
                "Requires owner approval before changing merchandising rules in production.",
            ],
            "decisionRecord": "Stores the conflict evidence, proposed rule diff, approval signature, and monitoring outcome. Private chain-of-thought is not stored.",
        },
        "temporal": {
            "workflowId": "temporal/mxp-governance/ops-7b19",
            "cadence": "Runs every 6 hours and immediately when exit-rate anomaly exceeds threshold.",
            "retryPolicy": "Retry rule snapshot and shadow replay twice; never retry production mutation without approval.",
            "sla": "Manual approval due within 1 business hour for high-risk merchandising conflicts.",
            "checkpoints": [
                "Rule conflict capture",
                "Owner approval request",
                "Shadow relevance replay",
                "Canary traffic gate",
                "Rollback snapshot retention",
            ],
        },
        "humanApproval": {
            "mode": "required",
            "owner": "Search lead: Priya Menon",
            "status": "Pending",
            "reason": "High-risk merchandising rule change touches promoted inventory and revenue ordering.",
            "expiry": "Approval expires 1 business hour after request.",
            "record": "A signed human approval must be recorded before canary deployment.",
        },
        "monitoringSignals": [
            {"label": "Conversion risk", "value": "14% drop", "status": "blocked", "detail": "Current rule pins stale inventory above better matches."},
            {"label": "Inventory health", "value": "3 units", "status": "watch", "detail": "Low stock on pinned clearance SKU creates poor landing experience."},
            {"label": "Rollback snapshot", "value": "v1.0.4", "status": "healthy", "detail": "Baseline rule state is retained for emergency reset."},
        ],
        "feedbackLoop": "Post-approval canary feedback compares conversion, exit rate, and SKU availability before promotion beyond 25% traffic.",
        "liveMetrics": {
            "queryVolume": 9100,
            "exitRate": 14,
            "revenueLoss": 3500,
            "baselineNdcg": 0.63,
            "proposedNdcg": 0.88,
            "p95Latency": 124,
        },
        "accent": "#2F5D50",
        "accentGlow": "rgba(47,93,80,0.12)",
        "accentBorder": "rgba(47,93,80,0.25)",
        "beforeQuery": "winter jacket clearance",
        "beforeResults": [
            {"name": "Last Season Parka (Clearance)", "price": 45, "stock": 3, "detail": "pinned #1 by MXP rule"},
            {"name": "Old Fleece Vest (Clearance)", "price": 22, "stock": 1, "detail": "pinned #2 by MXP rule"},
        ],
        "afterResults": [
            {"name": "Alpine Down Jacket 2025", "price": 189, "stock": 42, "score": "0.93"},
            {"name": "ThermoShell Pro Coat", "price": 149, "stock": 28, "score": "0.90"},
            {"name": "Last Season Parka (Clearance)", "price": 45, "stock": 3, "score": "0.72"},
        ],
    },
]


QUERY_CLUSTERS = [
    {
        "query": "waterproof trail shoes",
        "volume": "12,800",
        "exits": "18%",
        "loss": "-$4,200",
        "impact": "High",
        "tag": "Catalog attribute gap",
        "badgeClass": "waterproof",
        "status": "Active Runbook (ops-4f72)",
    },
    {
        "query": "hydra p / hydra pack",
        "volume": "5,400",
        "exits": "32%",
        "loss": "-$2,100",
        "impact": "Med",
        "tag": "Typo synonym miss",
        "badgeClass": "typo",
        "status": "Active Runbook (ops-1a88)",
    },
    {
        "query": "winter jacket clearance",
        "volume": "9,100",
        "exits": "14%",
        "loss": "-$3,500",
        "impact": "Med",
        "tag": "MXP Boost conflict",
        "badgeClass": "rules",
        "status": "Active Runbook (ops-7b19)",
    },
    {
        "query": "voice: hiking boots goretex",
        "volume": "2,800",
        "exits": "42%",
        "loss": "-$1,800",
        "impact": "Med",
        "tag": "Multimodal image QA",
        "badgeClass": "waterproof",
        "status": "Shadow Test Queued",
    },
    {
        "query": "running jackets lightweight",
        "volume": "15,200",
        "exits": "4%",
        "loss": "-$400",
        "impact": "Low",
        "tag": "Healthy relevance",
        "badgeClass": "rules",
        "status": "Auto-closed (Healthy)",
    },
]


AUDIT_ROWS = [
    {
        "time": "backend",
        "runbookId": "ops-4f72",
        "title": 'Catalog Enrichment — "Waterproof" Attribute Gap',
        "action": "Backend data loaded into UI",
        "approver": "system:fastapi",
        "agentName": "Catalog Optimization Agent",
        "agentBehavior": "Clusters failed queries against product taxonomy gaps.",
        "temporalWorkflowId": "temporal/catalog-gap/ops-4f72",
        "approvalGate": "Approval not requested: policy gates pass.",
        "monitoringSummary": "NDCG delta: +0.31 (healthy); P95 latency: 118ms (healthy)",
        "feedbackRecord": "Backend source-of-truth payload available to frontend.",
        "recordType": "monitoring",
        "hash": "sha256:backend",
        "isRollback": False,
    }
]


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
        "temporal_workflows_url": TEMPORAL_WORKFLOWS_URL,
        "endpoints": {
            "health": "/health",
            "runbooks": "/api/runbooks",
            "audit": "/api/audit",
            "query_clusters": "/api/query-clusters",
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
        "temporal_workflows_url": TEMPORAL_WORKFLOWS_URL,
    }


@app.get("/api/temporal", response_model=TemporalLink)
def get_temporal_link() -> TemporalLink:
    return TemporalLink(
        namespace="default",
        workflows_url=TEMPORAL_WORKFLOWS_URL,
        redirect_endpoint="/api/temporal/workflows",
    )


@app.get("/api/temporal/details", response_model=TemporalDetails)
def get_temporal_details() -> TemporalDetails:
    workflows = [
        TemporalWorkflowSummary(
            runbook_id=runbook["id"],
            title=runbook["title"],
            workflow_id=runbook["temporal"]["workflowId"],
            status=runbook["status"],
            cadence=runbook["temporal"]["cadence"],
            retry_policy=runbook["temporal"]["retryPolicy"],
            sla=runbook["temporal"]["sla"],
            checkpoints=runbook["temporal"]["checkpoints"],
        )
        for runbook in RUNBOOKS
    ]

    return TemporalDetails(
        namespace="default",
        status="configured",
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


@app.get("/api/runbooks")
def get_runbooks() -> list[dict]:
    return deepcopy(RUNBOOKS)


@app.get("/api/audit")
def get_audit() -> list[dict]:
    return deepcopy(AUDIT_ROWS)


@app.get("/api/query-clusters")
def get_query_clusters() -> list[dict]:
    return deepcopy(QUERY_CLUSTERS)


@app.post("/api/runbooks/{runbook_id}/actions/{action}", response_model=RunbookActionResponse)
def run_runbook_action(
    runbook_id: str,
    action: Literal["evaluate", "release", "rollback"],
) -> RunbookActionResponse:
    status_by_action = {
        "evaluate": "Shadow Test",
        "release": "Released",
        "rollback": "Rolled Back",
    }

    runbook = next((item for item in RUNBOOKS if item["id"] == runbook_id), None)
    if runbook is not None:
        runbook["status"] = status_by_action[action]
        AUDIT_ROWS.insert(
            0,
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "runbookId": runbook["id"],
                "title": runbook["title"],
                "action": f"Backend queued {action} action",
                "approver": "system:fastapi",
                "agentName": runbook["agent"]["name"],
                "agentBehavior": runbook["agent"]["behaviors"][0],
                "temporalWorkflowId": runbook["temporal"]["workflowId"],
                "approvalGate": runbook["humanApproval"]["record"],
                "monitoringSummary": "; ".join(
                    f"{signal['label']}: {signal['value']} ({signal['status']})"
                    for signal in runbook["monitoringSignals"]
                ),
                "feedbackRecord": runbook["feedbackLoop"],
                "recordType": "rollback" if action == "rollback" else "release" if action == "release" else "evaluation",
                "hash": f"sha256:fastapi-{runbook_id}-{action}",
                "isRollback": action == "rollback",
            },
        )

    return RunbookActionResponse(
        runbook_id=runbook_id,
        action=action,
        status="queued",
        temporal_workflows_url=TEMPORAL_WORKFLOWS_URL,
        message=(
            "Action accepted by FastAPI bridge. Use temporal_workflows_url "
            "to inspect the workflow in Temporal Web."
        ),
    )
