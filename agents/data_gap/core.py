# Runbook_System_Final/agents/data_gap/core.py
"""Agent to identify data gaps and preventative measures."""
from typing import List, Dict, Any
from shared.schemas import OpsSignal, RootCauseReport, ImpactAnalysis, PreventionPlan
from orchestration import RLMClient
import json

class DataGapAgent:
    """
    The DataGapAgent identifies missing data quality tests and monitoring gaps
    based on the root cause and impact analysis using the RLM.
    """
    def __init__(self, rlm_client: RLMClient):
        self.rlm_client = rlm_client
        print("[DataGapAgent]: Initialized with RLMClient.")

    async def run(self, signal: OpsSignal, root_cause_report: RootCauseReport, impact_analysis: ImpactAnalysis) -> PreventionPlan:
        """Identify data gaps using RLM."""
        print(f"[DataGapAgent]: Identifying data gaps for signal {signal.signal_id}...")

        incident_brief = f"""
        Task: Identify missing data quality tests and monitoring gaps based on this failure.
        Affected Capability: {root_cause_report.affected_capability}
        Root Cause: {root_cause_report.root_cause}
        Business Impact: {impact_analysis.business_impact}
        Signal Summary: {signal.summary}
        Raw Data: {json.dumps(signal.raw_data, indent=2)}
        """
        
        # Use the RLM client to process the incident brief
        state = await self.rlm_client.process(incident_brief, preset="medium")
        final_synthesis = state.get("final_result", "")
        
        # Example of RLM-recommended prevention plans
        recommended_tests = [f"[RLM Recommended Test]: {final_synthesis[:100]}..."] # Truncate for brevity
        recommended_monitoring = [f"Add monitoring to detect '{root_cause_report.affected_capability}' regressions."]

        print(f"[DataGapAgent]: Data gaps identified for {signal.signal_id}.")

        return PreventionPlan(
            signal_id=signal.signal_id,
            missing_data_quality_tests=recommended_tests,
            monitoring_gaps=recommended_monitoring
        )
