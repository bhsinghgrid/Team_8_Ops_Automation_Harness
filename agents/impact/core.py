# Runbook_System_Final/agents/impact/core.py
"""Agent to assess the business impact of a root cause."""
from typing import List, Dict, Any
from Runbook_System_Final.shared.schemas import OpsSignal, RootCauseReport, ImpactAnalysis
from Runbook_System_Final.orchestration.rlm_client import RLMClient
from Runbook_System_Final.tools import impact_tools, owner_tools
import json

class CapabilityImpactAgent:
    """
    The CapabilityImpactAgent assesses the business and operational consequences
    of an identified root cause using the RLM and impact tools.
    """
    def __init__(self, rlm_client: RLMClient):
        self.rlm_client = rlm_client
        print("[CapabilityImpactAgent]: Initialized with RLMClient and Tools.")

    async def run(self, signal: OpsSignal, root_cause_report: RootCauseReport) -> ImpactAnalysis:
        """Assess business impact using RLM and specialized tools."""
        print(f"[CapabilityImpactAgent]: Assessing impact for signal {signal.signal_id}...")

        # 1. Use deterministic tools to score the impact
        impact_score = impact_tools.score_signal(signal.raw_data)
        
        # 2. Use owner tools to identify the correct primary and secondary teams
        inferred_cap = impact_tools.signal_to_capability(signal.raw_data)
        owner_info = owner_tools.CAPABILITY_OWNERS.get(inferred_cap, {"primary_owner": "Search Team"})
        
        incident_brief = f"""
        Task: Assess the business impact and blast radius of this search failure.
        Affected Capability: {root_cause_report.affected_capability}
        Root Cause: {root_cause_report.root_cause}
        Signal Summary: {signal.summary}
        Inferred Impact Score: {impact_score} (calculated via tools)
        Suggested Owner: {owner_info.get('primary_owner')}
        Raw Data: {json.dumps(signal.raw_data, indent=2)}
        """
        
        # Use the RLM client to process the incident brief
        state = await self.rlm_client.process(incident_brief, preset="medium")
        final_synthesis = state.get("final_result", "")
        
        # Check for RLM Error
        is_rlm_error = "RLM Failure" in final_synthesis or "API Key Missing" in final_synthesis or "RLM JSON decoding failure" in final_synthesis or "error" in final_synthesis.lower()

        # Combine tools with AI results
        suggested_dashboards = ["Conversion Metrics", "Zero-Result Analytics"]
        suggested_teams = [owner_info.get("primary_owner")]
        if owner_info.get("secondary_owner"):
            suggested_teams.append(owner_info.get("secondary_owner"))

        if is_rlm_error or not final_synthesis.strip():
            business_impact_desc = f"[Tool-Based Assessment]: High impact detected in {inferred_cap} with score {impact_score}."
        else:
            business_impact_desc = f"[RLM Assessed (Score: {impact_score})]: {final_synthesis[:500]}..."

        print(f"[CapabilityImpactAgent]: Impact assessed for {signal.signal_id}.")
        
        return ImpactAnalysis(
            signal_id=signal.signal_id,
            business_impact=business_impact_desc,
            affected_dashboards=suggested_dashboards,
            affected_teams=list(set(suggested_teams))
        )
