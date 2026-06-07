# Runbook_System_Final/agents/fix_plan/core.py
"""Agent to synthesize the final fix plan and governance."""
import uuid
import json
from typing import List, Dict, Any
from shared.schemas import OpsSignal, RootCauseReport, ImpactAnalysis, PreventionPlan, EvalReport, Runbook, RunbookStatus, RunbookApprovalStatus # Added RunbookStatus, RunbookApprovalStatus
from orchestration import RLMClient # Import RLMClient from package namespace
from tools import owner_tools, approval_tools

class FixPlanAgent:
    """
    The FixPlanAgent synthesizes the final immediate fix plan, assigns ownership,
    and determines approval requirements using the RLM and governance tools.
    """
    def __init__(self, rlm_client: RLMClient):
        self.rlm_client = rlm_client
        print("[FixPlanAgent]: Initialized with RLMClient.")

    async def run(self, signal: OpsSignal, root_cause: RootCauseReport, impact: ImpactAnalysis, prevention: PreventionPlan, eval_report: EvalReport) -> Runbook:
        """Generate final runbook using RLM."""
        print(f"[FixPlanAgent]: Generating fix plan for signal {signal.signal_id}...")

        incident_brief = f"""
        Task: Draft a step-by-step remediation runbook for the engineering team based on the following analysis.
        Root Cause: {root_cause.root_cause}
        Affected Capability: {root_cause.affected_capability}
        Business Impact: {impact.business_impact}
        Eval State: {eval_report.assessment_state}
        Eval Confidence: {eval_report.confidence_score}
        Missing Tests: {json.dumps(prevention.missing_data_quality_tests, indent=2)}
        Monitoring Gaps: {json.dumps(prevention.monitoring_gaps, indent=2)}
        Signal Summary: {signal.summary}
        Raw Data: {json.dumps(signal.raw_data, indent=2)}
        """
        
        state = await self.rlm_client.process(incident_brief, preset="high") # Using await for RLM call
        final_synthesis = state.get("final_result", "")

        # Governance and Ownership
        capability_key = root_cause.affected_capability.lower()
        mapped_key = "search_relevance"
        if "catalog" in capability_key: mapped_key = "catalog"
        elif "mxp" in capability_key or "merchandising" in capability_key: mapped_key = "merchandising_rules"
        elif "infrastructure" in capability_key or "vector" in capability_key: mapped_key = "vector_platform"
        elif "autocomplete" in capability_key: mapped_key = "autocomplete"

        owner_info = owner_tools.CAPABILITY_OWNERS.get(mapped_key, {"primary_owner": "Search Lead"})
        owner = owner_info.get("primary_owner", "Search Lead")
        needs_approval = approval_tools.requires_human_approval(root_cause.affected_capability, impact.business_impact)

        print(f"[FixPlanAgent]: Fix plan generated for {signal.signal_id}. Owner: {owner}, Approval Required: {needs_approval}")

        return Runbook(
            runbook_id=f"runbook-{uuid.uuid4()}",
            signal=signal,
            root_cause=root_cause,
            impact=impact,
            prevention=prevention,
            eval_report=eval_report,
            immediate_fix_plan=[
                f"[RLM Proposed Fix Phase 1]: {final_synthesis[:100]}...", # Truncate for brevity
                f"[RLM Proposed Fix Phase 2]: {final_synthesis[100:200]}..." # Truncate for brevity
            ],
            owner=owner,
            approval_required=needs_approval,
            status=RunbookStatus.DRAFT, # Initial status
            approval_status=RunbookApprovalStatus.PENDING if needs_approval else RunbookApprovalStatus.APPROVED # Initial approval status
        )
