import json
from typing import Any


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


def readable_text(value: Any, default: str = "") -> str:
    if value in (None, ""):
        return default

    if isinstance(value, list):
        items = [readable_text(item) for item in value]
        return "; ".join(item for item in items if item) or default

    if isinstance(value, dict):
        for key in (
            "root_cause",
            "business_impact",
            "problem_statement",
            "problem",
            "fix_summary",
            "summary",
            "description",
            "text",
            "step",
            "action",
            "title",
            "value",
        ):
            nested_value = value.get(key)
            if nested_value not in (None, ""):
                return readable_text(nested_value, default)
        return json.dumps(value, default=str)

    return str(value)


def numeric_like(value: Any) -> bool:
    if isinstance(value, (int, float)):
        return True
    if not isinstance(value, str):
        return False

    value_as_text = value.strip().replace(",", "").replace("%", "")
    if not value_as_text:
        return False

    try:
        float(value_as_text)
    except ValueError:
        return False
    return True


def first_text_value(
    runbook: dict,
    *keys: str,
    default: str = "",
    allow_numeric: bool = True,
) -> str:
    for key in keys:
        value = get_runbook_value(runbook, key, default=None)
        if value in (None, "", []):
            continue

        text = readable_text(value)
        if text and (allow_numeric or not numeric_like(text)):
            return text

    return default


def first_text_list_value(runbook: dict, *keys: str, default: list[str] | None = None) -> list[str]:
    for key in keys:
        value = get_runbook_value(runbook, key, default=None)
        if value in (None, "", []):
            continue

        raw_items = value if isinstance(value, list) else [value]
        items = [readable_text(item) for item in raw_items]
        cleaned_items = [item for item in items if item]
        if cleaned_items:
            return cleaned_items

    return default or []


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
    description = first_text_value(
        runbook,
        "description",
        "summary",
        "problem_statement",
        "problemStatement",
        default="No description provided.",
    )
    root_cause = first_text_value(
        runbook,
        "rootCause",
        "root_cause.root_cause",
        "root_cause.summary",
        "root_cause.description",
        "analysis.root_cause",
        "rca.root_cause",
        "root_cause",
        default="Root cause was not provided by the backend payload.",
        allow_numeric=False,
    )
    business_impact_summary = first_text_value(
        runbook,
        "businessImpactSummary",
        "business_impact_summary",
        "businessImpactText",
        "business_impact_text",
        "impact.business_impact",
        "impact.summary",
        "impact.description",
        "impactAnalysis.business_impact",
        "impact_analysis.business_impact",
        "business_impact.description",
        "business_impact.summary",
        "business_impact",
        default="Business impact details were not provided by the backend payload.",
        allow_numeric=False,
    )
    problem_statement = first_text_value(
        runbook,
        "problemStatement",
        "problem_statement",
        "problem",
        "issue",
        "incident.problem",
        "incident.summary",
        default=description,
        allow_numeric=False,
    )
    fix_summary = first_text_value(
        runbook,
        "fixSummary",
        "fix_summary",
        "problemFixing",
        "problem_fixing",
        "fix",
        "resolution",
        "fixPlan.summary",
        "fix_plan.summary",
        "runbook.fix_summary",
        default="Fix summary was not provided by the backend payload.",
        allow_numeric=False,
    )
    fix_plan_steps = first_text_list_value(
        runbook,
        "fixPlanSteps",
        "fix_plan_steps",
        "immediate_fix_plan",
        "fixPlan.steps",
        "fix_plan.steps",
        "fix_plan",
        "runbook.immediate_fix_plan",
        "actions",
        default=[],
    )
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
        "description": description,
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
        "rootCause": root_cause,
        "businessImpactSummary": business_impact_summary,
        "problemStatement": problem_statement,
        "fixSummary": fix_summary,
        "fixPlanSteps": fix_plan_steps,
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
    # Handle both remote format and local query_clusters.json format
    query = str(row.get("query") or row.get("cluster") or "unknown")
    volume = str(row.get("volume") or row.get("monthly_volume") or row.get("count") or "0")
    
    # Exits: if exits is not provided, generate a plausible one or default to "15%"
    exits = str(row.get("exits") or row.get("exit_rate") or "15%")
    
    # Loss: handle both remote format and local normalizedRevenueImpact
    loss_val = row.get("loss") or row.get("revenue_loss")
    if not loss_val:
        impact_val = row.get("normalizedRevenueImpact")
        if impact_val is not None:
            loss_val = f"${impact_val}"
        else:
            loss_val = "$0"
    loss = str(loss_val)
    
    # Impact: handle both remote and calculated
    impact = row.get("impact") or row.get("impact_rank")
    if not impact:
        try:
            val = float(str(row.get("normalizedRevenueImpact", 0)))
            if val >= 5000:
                impact = "High"
            elif val >= 2000:
                impact = "Med"
            else:
                impact = "Low"
        except Exception:
            impact = "Low"
    impact = allowed_value(impact, {"High", "Med", "Low"}, "Low")
    
    # Tag: handle issue_type, themes, etc.
    tag = row.get("tag") or row.get("issue_type")
    if not tag:
        themes = row.get("themes")
        if isinstance(themes, list) and themes:
            tag = themes[0].title()
        else:
            tag = "Unclassified"
    tag = str(tag)
    
    # Badge class
    badge_class = row.get("badgeClass") or row.get("badge_class")
    if not badge_class:
        themes = [str(t).lower() for t in row.get("themes", [])]
        if "rules" in themes:
            badge_class = "rules"
        elif "typo" in themes:
            badge_class = "typo"
        else:
            badge_class = "waterproof"
    badge_class = allowed_value(badge_class, {"waterproof", "typo", "rules"}, "rules")
    
    status = str(row.get("status") or "not triaged")
    
    return {
        "query": query,
        "volume": volume,
        "exits": exits,
        "loss": loss,
        "impact": impact,
        "tag": tag,
        "badgeClass": badge_class,
        "status": status,
    }


def status_from_temporal_workflow(status: str) -> str:
    status_map = {
        "RUNNING": "Shadow Test",
        "COMPLETED": "Released",
        "FAILED": "Rollback Candidate",
        "TERMINATED": "Rolled Back",
        "CANCELED": "Rolled Back",
        "TIMED_OUT": "Rollback Candidate",
    }
    return status_map.get(status.upper(), "Eval Ready")
