# Runbook_System_Final/agents/impact/core.py
"""Agent to assess the business impact of a root cause."""
from typing import List, Dict, Any
from shared.schemas import OpsSignal, RootCauseReport, ImpactAnalysis
from orchestration import RLMClient

class CapabilityImpactAgent:
    """
    The CapabilityImpactAgent assesses the business and operational consequences
    of an identified root cause using the RLM.
    """
    def __init__(self, rlm_client: RLMClient):
        self.rlm_client = rlm_client
        print("[CapabilityImpactAgent]: Initialized with RLMClient.")

    async def run(self, signal: OpsSignal, root_cause_report: RootCauseReport) -> ImpactAnalysis:
        """Assess business impact using RLM."""
        print(f"[CapabilityImpactAgent]: Assessing impact for signal {signal.signal_id}...")

        incident_brief = f"""
        Task: Assess the business impact and blast radius of this search failure.
        Affected Capability: {root_cause_report.affected_capability}
        Root Cause: {root_cause_report.root_cause}
        Signal Summary: {signal.summary}
        Raw Data: {json.dumps(signal.raw_data, indent=2)}
        """
        
        # Use the RLM client to process the incident brief
        state = await self.rlm_client.process(incident_brief, preset="medium")
        final_synthesis = state.get("final_result", "")
        
        # Example of how RLM might suggest affected dashboards/teams
        suggested_dashboards = ["Conversion Metrics", "Zero-Result Analytics"]
        suggested_teams = ["Product Search Team"]

        print(f"[CapabilityImpactAgent]: Impact assessed for {signal.signal_id}.")
        
        return ImpactAnalysis(
            signal_id=signal.signal_id,
            business_impact=f"[RLM Assessed]: {final_synthesis[:200]}...", # Truncate for brevity
            affected_dashboards=suggested_dashboards,
            affected_teams=suggested_teams
        )
