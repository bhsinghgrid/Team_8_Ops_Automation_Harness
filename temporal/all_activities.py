# temporal/all_activities.py
from temporalio import activity
import json
import uuid
import sys
import asyncio
from typing import List, Dict, Any, Optional
import logging
import random
from pathlib import Path
from enum import Enum
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from elasticsearch import Elasticsearch
from dotenv import load_dotenv, find_dotenv
import os
from google import genai
from prometheus_client import Histogram, Counter
import httpx

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add workspace root to sys.path for tool imports if not present
workspace_root = str(Path(__file__).resolve().parents[1])
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

# Import existing tools for Agent enrichment
try:
    from Runbook_System_Final.tools import (
        capability_mapping_tools, 
        signal_tools, 
        impact_tools, 
        owner_tools, 
        data_gap_tools,
        index_analysis_tools,
        stale_embedding_tools,
        synonym_tools
    )
except ImportError:
    logger.warning("⚠️ Could not import Runbook_System_Final tools. Some agent logic will be degraded.")
    capability_mapping_tools = None
    signal_tools = None
    impact_tools = None
    owner_tools = None
    data_gap_tools = None
    index_analysis_tools = None
    stale_embedding_tools = None
    synonym_tools = None

# --- Schemas ---
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
    signal_id: str
    signal_type: str
    summary: str
    severity: str = "medium"
    category: Optional[str] = None
    affected_entities: List[str] = []
    raw_data: Dict[str, Any]
    model_config = {"extra": "allow"}

class RootCauseReport(BaseModel):
    signal_id: str
    root_cause: str
    affected_capability: str
    evidence: List[str]

class ImpactAnalysis(BaseModel):
    signal_id: str
    business_impact: str
    affected_dashboards: List[str] = []
    affected_teams: List[str] = []

class PreventionPlan(BaseModel):
    signal_id: str
    missing_data_quality_tests: List[str] = []
    monitoring_gaps: List[str] = []

class EvalReport(BaseModel):
    signal_id: str
    assessment_state: str
    confidence_score: float
    shadow_metrics: Dict[str, Any] = {}
    eval_summary: str

class Runbook(BaseModel):
    runbook_id: str
    signal: OpsSignal
    root_cause: RootCauseReport
    impact: ImpactAnalysis
    prevention: PreventionPlan
    eval_report: EvalReport
    immediate_fix_plan: List[str]
    owner: str
    approval_required: bool
    status: RunbookStatus = RunbookStatus.DRAFT
    approval_status: RunbookApprovalStatus = RunbookApprovalStatus.PENDING

# --- Clients ---
class RLMClient:
    def __init__(self):
        load_dotenv(find_dotenv(str(Path.cwd() / ".env")))
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    async def process(self, user_prompt: str):
        if not self.client: return {"final_result": "API Key Missing", "confidence": 0.0}
        try:
            response = await asyncio.to_thread(self.client.models.generate_content, model="gemini-2.5-flash", contents=user_prompt)
            return {"final_result": response.text.strip(), "confidence": 0.85}
        except Exception as e: return {"final_result": f"Error: {e}", "confidence": 0.0}

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    ELASTICSEARCH_URL: str = "http://localhost:9200"

settings = Settings()

# --- Shared Settings & Data ---

# Path to the real ground truth judgments file
RELEVANCE_JUDGMENTS_FILE = "/Users/bhsingh/Documents/Backend/magellan_signal_ingestion_backend/mock-data/relevance_judgments.json"

def load_real_ground_truth() -> Dict[str, Dict[str, int]]:
    """Loads search relevance judgments from the real golden dataset file."""
    try:
        with open(RELEVANCE_JUDGMENTS_FILE, "r") as f:
            data = json.load(f)
            return data.get("judgments", {})
    except Exception as e:
        logger.warning(f"⚠️ Could not load real ground truth file: {e}. Using internal mock fallback.")
        return {
            "waterproof trail shoes": {"FOOT-001": 3, "FOOT-006": 2, "FOOT-012": 3},
            "Smart Watches": {"watch_pro_1": 3, "watch_lite_2": 2}
        }

# Initialize GROUND_TRUTH from the real data file
GROUND_TRUTH = load_real_ground_truth()

# --- Prometheus Metrics ---
SEARCH_LATENCY = Histogram(
    'shadow_pipeline_latency_seconds', 
    'Latency of candidate search pipeline in seconds',
    buckets=[0.05, 0.1, 0.15, 0.2, 0.3, 0.5] 
)

SHADOW_NDCG_SCORE = Histogram(
    'shadow_pipeline_ndcg_score',
    'NDCG score of candidate search pipeline',
    buckets=[0.5, 0.7, 0.8, 0.84, 0.9, 0.95, 1.0]
)

# --- Traffic Shadowing ---
DIFFY_PROXY_URL = "http://localhost:31900/search"

async def call_diffy_proxy(query: str):
    """
    Sends a search request to the Diffy Proxy.
    Diffy then mirrors this traffic to primary, secondary, and candidate.
    """
    logger.info(f"📡 Mirroring traffic to Diffy Proxy for query: '{query[:50]}...'")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                DIFFY_PROXY_URL, 
                params={"q": query}, 
                timeout=15.0,
                headers={"Canonical-Query": "shadow-test"} 
            )
            if response.status_code == 200:
                logger.info(f"✅ Diffy Proxy accepted and mirrored the request.")
                return response.json()
            else:
                logger.warning(f"⚠️ Diffy Proxy returned status {response.status_code}")
                return None
    except Exception:
        logger.exception("❌ Failed to communicate with Diffy Proxy")
        return None

async def get_production_baseline(query: str) -> Dict[str, int]:
    """
    Fetches the production (Primary) search results to use as a proxy ground truth.
    This is used when a query is not present in the Golden Dataset.
    """
    logger.info(f"🔍 Querying Production (Primary) for baseline: '{query}'")
    # In a real environment, we would call the 'primary' service from Diffy
    # For now, we simulate a call to the Primary instance in the Diffy cluster
    try:
        async with httpx.AsyncClient() as client:
            # Note: 'primary' is the service name in docker-compose.yml
            # If running locally, it might be localhost:8080
            url = "http://localhost:8080/search" 
            response = await client.get(url, params={"q": query}, timeout=5.0)
            if response.status_code == 200:
                results = response.json().get("results", [])
                # Convert list of results to a relevance map (e.g., top results are highly relevant)
                return {res["id"]: 3 - min(idx, 3) for idx, res in enumerate(results[:3])}
    except Exception:
        pass
    return {}

def execute_candidate_pipeline(query: str):
    """Simulates executing the search query against the candidate patch."""
    import time
    start_time = time.time()
    
    # Simulate search execution latency (e.g., 110ms)
    time.sleep(0.11) 
    
    # Mock search results returned by the pipeline variant being tested
    mock_results = {
        "waterproof trail shoes": ["prod_alpha_goretex", "prod_beta_waterresistant", "prod_gamma_sandal"],
        "catalog_update_failure": ["Electronics_Item_1", "Electronics_Item_2", "Old_Item"]
    }
    
    latency = time.time() - start_time
    return mock_results.get(query, []), latency

def requires_human_approval(capability: str, severity: str) -> bool:
    if severity.upper() == "CRITICAL": return True
    if "catalog" in capability.lower(): return False
    return True

# --- Activities ---

@activity.defn
async def generate_signal_from_elasticsearch() -> OpsSignal:
    client = Elasticsearch(settings.ELASTICSEARCH_URL)
    # Simplified query to ensure we get the latest signal regardless of mapping
    query = {"query": {"match_all": {}}, "size": 1}
    try:
        # Search specifically in the signals index
        res = client.search(index="magellan-signals", body=query)
        hits = res.get("hits", {}).get("hits", [])
        if hits:
            data = hits[0]["_source"]
            logger.info(f"🎯 Successfully fetched real signal from ES: {data.get('message')}")
        else:
            logger.warning("⚠️ No signals found in 'magellan-signals' index. Falling back to mock.")
            data = {"message": "Mock: Missing attribute", "event": {"kind": "mock"}}
    except Exception as e:
        logger.error(f"❌ ES Search failed: {e}")
        data = {"message": f"Error: {str(e)}", "event": {"kind": "error"}}
    
    return OpsSignal(
        signal_id=f"es-signal-{uuid.uuid4().hex[:8]}",
        signal_type=data.get("event", {}).get("kind", "unknown"),
        summary=data.get("message", ""),
        severity="CRITICAL" if "CRITICAL" in str(data.get("message")).upper() else "MEDIUM",
        raw_data=data
    )

@activity.defn
async def root_cause_activity(signal: OpsSignal) -> RootCauseReport:
    rlm = RLMClient()
    
    # Use existing tools to enrich the RLM prompt
    inferred_capability = "unknown"
    capability_family = "unknown"
    if capability_mapping_tools:
        inferred_capability = capability_mapping_tools.infer_capability_from_signal(signal.raw_data)
        capability_family = capability_mapping_tools.capability_family(signal.signal_type, inferred_capability)
        
    prompt = f"""
    Task: Decompose this operational signal, analyze the symptom, and compose a final root cause and affected capability.
    Inferred Capability: {inferred_capability} ({capability_family})
    Signal Type: {signal.signal_type}
    Summary: {signal.summary}
    Raw Data: {json.dumps(signal.raw_data)}
    """
    
    res = await rlm.process(prompt)
    
    # Final capability string
    final_cap = inferred_capability.replace("_", " ").title() if inferred_capability != "unknown" else "Search API Handling"
    
    return RootCauseReport(
        signal_id=signal.signal_id, 
        root_cause=str(res["final_result"]), 
        affected_capability=final_cap, 
        evidence=[f"raw_signal_{signal.signal_id}.json", f"Tool Match: {inferred_capability}"]
    )

@activity.defn
async def impact_activity(signal: OpsSignal, root_cause: RootCauseReport) -> ImpactAnalysis:
    rlm = RLMClient()
    
    # Use deterministic tools to score impact and find owners
    impact_score = 0
    suggested_teams = ["Search Team"]
    inferred_cap = "unknown"
    
    if impact_tools and owner_tools:
        impact_score = impact_tools.score_signal(signal.raw_data)
        inferred_cap = impact_tools.signal_to_capability(signal.raw_data)
        owner_info = owner_tools.CAPABILITY_OWNERS.get(inferred_cap, {})
        if owner_info.get("primary_owner"):
            suggested_teams = [owner_info.get("primary_owner")]
            if owner_info.get("secondary_owner"):
                suggested_teams.append(owner_info.get("secondary_owner"))
    
    # Ensure all suggested_teams are strings and not None
    suggested_teams = [str(t) for t in suggested_teams if t is not None]

    prompt = f"""
    Task: Assess the business impact and blast radius of this search failure.
    Affected Capability: {root_cause.affected_capability}
    Root Cause: {root_cause.root_cause}
    Signal Summary: {signal.summary}
    Calculated Impact Score: {impact_score}
    Suggested Owners: {', '.join(suggested_teams)}
    Raw Metadata: {json.dumps(signal.raw_data)}
    """
    
    res = await rlm.process(prompt)
    
    return ImpactAnalysis(
        signal_id=signal.signal_id, 
        business_impact=f"[Score: {impact_score}] {str(res['final_result'])}",
        affected_teams=suggested_teams,
        affected_dashboards=["Conversion Metrics", "Search Performance"]
    )

@activity.defn
async def data_gap_activity(signal: OpsSignal, root_cause: RootCauseReport, impact: ImpactAnalysis) -> PreventionPlan:
    rlm = RLMClient()
    
    # 1. Use tools to perform a multi-dimensional technical audit
    actions = []
    audit_findings = []
    
    if data_gap_tools:
        gap_type = "query_vocabulary_gap" if "semantic" in root_cause.affected_capability.lower() else "candidate_catalog_delta"
        query = signal.raw_data.get("metadata", {}).get("query", "unknown")
        actions = data_gap_tools.data_gap_actions(gap_type=gap_type, incident_query=query)
        
        # Deep audit: Check for Index Config regessions
        if index_analysis_tools:
            diff = index_analysis_tools.diff_index_settings(
                signal.raw_data.get("baseline_settings", {}),
                signal.raw_data.get("candidate_settings", {})
            )
            if diff: audit_findings.append(f"Config Audit: Regressions found in {list(diff.keys())}")
            
        # Deep audit: Check for Vector Staleness
        if stale_embedding_tools and "stale" in root_cause.root_cause.lower():
            # Perform real drift check if data is available in the signal
            drift_report = stale_embedding_tools.build_stale_embedding_report(signal.raw_data)
            if drift_report.get("verdict") == "stale":
                audit_findings.append(f"Vector Audit: Stale embeddings detected. {drift_report.get('reasons', [])}")
            else:
                audit_findings.append("Vector Audit: Embeddings verified as fresh.")

    prompt = f"""
    Task: Identify missing data quality tests and monitoring gaps.
    Technical Audit Findings: {'; '.join(audit_findings)}
    Root Cause: {root_cause.root_cause}
    Business Impact: {impact.business_impact}
    Tool-Suggested SOPs: {', '.join(actions)}
    """
    
    res = await rlm.process(prompt)
    
    return PreventionPlan(
        signal_id=signal.signal_id, 
        missing_data_quality_tests=actions[:2] + audit_findings,
        monitoring_gaps=[str(res["final_result"])]
    )

@activity.defn
async def eval_activity(signal: OpsSignal, root_cause: RootCauseReport) -> EvalReport:
    """
    Temporal activity for Phase 3: Evaluation & Shadow Factory.
    Uses Diffy Proxy for traffic shadowing and mirroring.
    Uses Ranx for NDCG calculation and verifies performance guardrails.
    Tracks metrics via Prometheus.
    """
    from ranx import Qrels, Run, evaluate
    logger.info(f"Running Real Eval (Shadow Factory) for signal {signal.signal_id}...")

    # Extract query from signal summary or raw data
    query = signal.raw_data.get("metadata", {}).get("query", "waterproof trail shoes")
    
    # 1. Start Shadowing via Diffy/Envoy Proxy
    diffy_result = await call_diffy_proxy(signal.summary)
    
    # 2. Run the shadow request against the candidate pipeline
    discovered_products, latency_seconds = execute_candidate_pipeline(query)
    latency_ms = latency_seconds * 1000
    
    # Record to Prometheus
    SEARCH_LATENCY.observe(latency_seconds)
    
    ndcg_score = 0.0
    assessment_state = "fail"
    
    # --- Real Ground Truth Logic ---
    # 1. Check if we have Golden Dataset judgments for this query
    query_gt = GROUND_TRUTH.get(query)
    
    # 2. Fallback: If not in Golden Dataset, fetch Production (Primary) results as Proxy GT
    if not query_gt:
        query_gt = await get_production_baseline(query)
        if query_gt:
            logger.info(f"✅ Using Production Baseline as Proxy Ground Truth for '{query}'")
        else:
            logger.warning(f"⚠️ No Ground Truth or Production Baseline available for '{query}'")

    if query_gt and discovered_products:
        run_dict = {"q1": {prod: 1.0 / (idx + 1) for idx, prod in enumerate(discovered_products)}}
        qrels_dict = {"q1": query_gt}
        
        qrels = Qrels(qrels_dict)
        run = Run(run_dict)
        
        ndcg_score = evaluate(qrels, run, "ndcg@3")
        SHADOW_NDCG_SCORE.observe(ndcg_score)
        
        # 3. Automation Routing Gate (Guardrails)
        if ndcg_score >= 0.84 and latency_ms <= 150:
            assessment_state = "pass"
            eval_summary = f"🚀 [GATE PASS] NDCG@3: {ndcg_score:.2f} | Latency: {latency_ms:.1f}ms. Within thresholds."
        else:
            assessment_state = "fail"
            eval_summary = f"⚠️ [GATE FAIL] NDCG@3: {ndcg_score:.2f} | Latency: {latency_ms:.1f}ms. Below quality floor."
    elif not discovered_products:
        eval_summary = f"❌ [GATE FAIL] No products discovered for query '{query}'. Evaluation blocked."
    else:
        eval_summary = f"⚠️ [GATE BLOCKED] No Ground Truth data available to evaluate '{query}'."

    return EvalReport(
        signal_id=signal.signal_id,
        assessment_state=assessment_state,
        confidence_score=0.92 if assessment_state == "pass" else 0.45,
        shadow_metrics={
            "ndcg_v_prod": ndcg_score,
            "latency_p95_ms": latency_ms,
            "query": query,
            "result_count": len(discovered_products)
        },
        eval_summary=eval_summary
    )

@activity.defn
async def fix_plan_activity(signal: OpsSignal, root_cause: RootCauseReport, impact: ImpactAnalysis, prevention: PreventionPlan, eval_report: EvalReport) -> Runbook:
    rlm = RLMClient()
    
    # 1. Determine Governance (Approval & Ownership)
    approval = requires_human_approval(root_cause.affected_capability, signal.severity)
    
    # Map capability to primary owner using owner_tools
    owner = "Search Lead"
    if owner_tools:
        # Normalize capability name for tool lookup
        cap_key = root_cause.affected_capability.lower().replace(" ", "_")
        owner_info = owner_tools.CAPABILITY_OWNERS.get(cap_key, {})
        owner = owner_info.get("primary_owner", "Search Lead")

    # 2. Synthesis: Generate the step-by-step fix plan using RLM
    prompt = f"""
    Task: Draft a step-by-step remediation runbook for the engineering team.
    Root Cause: {root_cause.root_cause}
    Affected Capability: {root_cause.affected_capability}
    Business Impact: {impact.business_impact}
    Eval Result: {eval_report.eval_summary} (Score: {eval_report.confidence_score})
    Prevention Suggestions: {', '.join(prevention.missing_data_quality_tests)}
    """
    
    res = await rlm.process(prompt)
    final_fix_text = str(res["final_result"])
    
    # Structure the fix plan into phases
    fix_plan_steps = [
        f"[Phase 1: Isolation]: {final_fix_text[:200]}...",
        f"[Phase 2: Remediation]: {final_fix_text[200:400]}...",
        "[Phase 3: Verification]: Execute canary monitoring and verify NDCG returns to baseline."
    ]

    return Runbook(
        runbook_id=f"runbook-{uuid.uuid4()}", 
        signal=signal, 
        root_cause=root_cause, 
        impact=impact,
        prevention=prevention, 
        eval_report=eval_report, 
        immediate_fix_plan=fix_plan_steps, 
        owner=owner,
        approval_required=approval, 
        status=RunbookStatus.GENERATED
    )

@activity.defn
async def suggest_tuning_activity(signal: OpsSignal, root_cause: RootCauseReport, impact: ImpactAnalysis) -> Dict[str, Any]:
    """
    Activity to run the SuggestTuningAgent.
    """
    from Runbook_System_Final.agents.suggest_tuning.core import SuggestTuningAgent
    agent = SuggestTuningAgent()
    tuning_pack = await agent.run(signal, root_cause, impact)
    return tuning_pack

@activity.defn
async def log_audit_activity(runbook_id: str, event: str, details: str):
    logger.info(f"[AUDIT] {runbook_id}: {event}")

@activity.defn
async def update_runbook_status_activity(runbook_id: str, status: str, message: str) -> str:
    logger.info(f"[STATUS] {runbook_id}: {status} - {message}")
    return "OK"

@activity.defn
async def send_approval_request_activity(runbook_id: str, owner: str, rc: str, ev: str) -> str:
    return "SENT"

@activity.defn
async def wait_for_approval_signal_activity(runbook_id: str, status: str) -> str:
    return status

@activity.defn
async def apply_fix_activity(runbook_id: str, steps: List[str]) -> str:
    return "APPLIED"

@activity.defn
async def monitor_canary_activity(runbook_id: str, metrics: Dict[str, Any]) -> str:
    return "SUCCESS"

@activity.defn
async def trigger_rollback_activity(runbook_id: str, reason: str, details: str) -> str:
    return "ROLLED_BACK"

ALL_ACTIVITIES = [
    generate_signal_from_elasticsearch,
    root_cause_activity,
    impact_activity,
    data_gap_activity,
    eval_activity,
    fix_plan_activity,
    log_audit_activity,
    update_runbook_status_activity,
    send_approval_request_activity,
    wait_for_approval_signal_activity,
    apply_fix_activity,
    monitor_canary_activity,
    trigger_rollback_activity,
    suggest_tuning_activity,
]
