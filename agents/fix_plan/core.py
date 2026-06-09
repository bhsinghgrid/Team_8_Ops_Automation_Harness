# Runbook_System_Final/agents/fix_plan/core.py
"""Agent to synthesize the final fix plan and governance."""
import uuid
import json
from typing import List, Dict, Any
from Runbook_System_Final.shared.schemas import OpsSignal, RootCauseReport, ImpactAnalysis, PreventionPlan, EvalReport, Runbook, RunbookStatus, RunbookApprovalStatus
from Runbook_System_Final.orchestration.rlm_client import RLMClient
from Runbook_System_Final.tools import owner_tools, approval_tools

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
        
        # Check for RLM Error
        is_rlm_error = "RLM Failure" in final_synthesis or "API Key Missing" in final_synthesis or "RLM JSON decoding failure" in final_synthesis or "error" in final_synthesis.lower()

        # Governance and Ownership
        capability_key = root_cause.affected_capability.lower()
        mapped_key = "search_relevance"
        if "catalog" in capability_key: 
            mapped_key = "catalog"
            fallback_steps = [
                "1. Isolate the affected catalog entities identified in the signal.",
                "2. Apply a targeted data patch to supply the missing attributes.",
                "3. Trigger a localized re-indexing and embedding refresh job for these entities.",
                "4. Verify the fix in staging using Shadow Traffic before promoting."
            ]
        elif "mxp" in capability_key or "merchandising" in capability_key: 
            mapped_key = "merchandising_rules"
            fallback_steps = [
                "1. Identify the conflicting merchandising rule.",
                "2. Temporarily disable or adjust the rule weight.",
                "3. Verify search relevance returns to baseline.",
            ]
        elif "infrastructure" in capability_key or "vector" in capability_key: 
            mapped_key = "vector_platform"
            fallback_steps = [
                "1. Investigate vector DB logs for synchronization errors.",
                "2. Force a full or partial sync from the primary data store.",
            ]
        elif "autocomplete" in capability_key: 
            mapped_key = "autocomplete"
            fallback_steps = [
                "1. Review recent vocabulary updates.",
                "2. Rollback to the previous stable vocabulary version if necessary.",
            ]
        else:
            fallback_steps = [
                "1. Triage the issue based on the root cause report.",
                "2. Apply standard mitigation procedures.",
            ]

        owner_info = owner_tools.CAPABILITY_OWNERS.get(mapped_key, {"primary_owner": "Search Lead"})
        owner = owner_info.get("primary_owner", "Search Lead")
        needs_approval = approval_tools.requires_human_approval(root_cause.affected_capability, impact.business_impact)

        print(f"[FixPlanAgent]: Fix plan generated for {signal.signal_id}. Owner: {owner}, Approval Required: {needs_approval}")

        if is_rlm_error or not final_synthesis.strip():
            final_fix_plan = [f"[Fallback Plan Step {i+1}]: {step}" for i, step in enumerate(fallback_steps)]
        else:
            # Basic chunking of the RLM output for steps
            final_fix_plan = [
                f"[RLM Proposed Fix Phase 1]: {final_synthesis[:250]}...",
                f"[RLM Proposed Fix Phase 2]: {final_synthesis[250:500]}..."
            ]

        return Runbook(
            runbook_id=f"runbook-{uuid.uuid4()}",
            signal=signal,
            root_cause=root_cause,
            impact=impact,
            prevention=prevention,
            eval_report=eval_report,
            immediate_fix_plan=final_fix_plan,
            owner=owner,
            approval_required=needs_approval,
            status=RunbookStatus.DRAFT, # Initial status
            approval_status=RunbookApprovalStatus.PENDING if needs_approval else RunbookApprovalStatus.APPROVED # Initial approval status
        )
