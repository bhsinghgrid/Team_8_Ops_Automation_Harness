# Runbook_System_Final/agents/data_gap/core.py
"""Agent to identify data gaps and preventative measures."""
from typing import List, Dict, Any
from Runbook_System_Final.shared.schemas import OpsSignal, RootCauseReport, ImpactAnalysis, PreventionPlan
from Runbook_System_Final.orchestration.rlm_client import RLMClient
from Runbook_System_Final.tools import data_gap_tools, index_analysis_tools, stale_embedding_tools, synonym_tools
import json

class DataGapAgent:
    """
    The DataGapAgent identifies missing data quality tests and monitoring gaps
    based on the root cause and impact analysis using the RLM and data gap tools.
    """
    def __init__(self, rlm_client: RLMClient):
        self.rlm_client = rlm_client
        print("[DataGapAgent]: Initialized with RLMClient and Tools.")

    async def run(self, signal: OpsSignal, root_cause_report: RootCauseReport, impact_analysis: ImpactAnalysis) -> PreventionPlan:
        """Identify data gaps using RLM and specialized tools."""
        print(f"[DataGapAgent]: Identifying data gaps for signal {signal.signal_id}...")

        # 1. Classify the gap using primary data gap tools
        query = signal.raw_data.get("metadata", {}).get("query", "unknown")
        metrics = signal.raw_data.get("metrics", {})
        gap_type = "unknown_gap"
        capability = root_cause_report.affected_capability.lower()

        if "catalog" in capability:
            gap_type = "candidate_catalog_delta" if metrics.get("affectedSkuCount", 0) > 0 else "query_vocabulary_gap"
        elif "embedding" in capability or "semantic" in capability:
            gap_type = "query_vocabulary_gap"
        
        # 2. Perform deep audits using specialized tools
        deep_audit_results = []
        
        # Check for search setting regressions
        if "settings" in str(signal.raw_data):
            diff = index_analysis_tools.diff_index_settings(
                signal.raw_data.get("baseline_settings", {}),
                signal.raw_data.get("candidate_settings", {})
            )
            if diff: deep_audit_results.append(f"Index Config Diff: {list(diff.keys())}")

        # Check for vector drift using the specialized staleness tool
        if "stale" in capability:
            # Pass the signal payload to build a real drift report
            drift_report = stale_embedding_tools.build_stale_embedding_report(signal.raw_data)
            if drift_report.get("verdict") == "stale":
                deep_audit_results.append(f"Vector Drift Audit: {drift_report.get('reasons', ['Unknown drift reason'])}")

        # Propose synonyms if it's a vocabulary gap
        if gap_type == "query_vocabulary_gap" and query != "unknown":
            # Using products and logs from raw_data if available
            catalog = signal.raw_data.get("catalog", [])
            logs = signal.raw_data.get("query_logs", [])
            synonyms = synonym_tools.propose_synonym_mappings(query, catalog, logs)
            if synonyms:
                deep_audit_results.append(f"Synonym Audit: Proposed {len(synonyms)} new mappings.")

        # Get suggested actions from base tools
        tool_actions = data_gap_tools.data_gap_actions(gap_type=gap_type, incident_query=query)

        incident_brief = f"""
        Task: Identify missing data quality tests and monitoring gaps.
        Inferred Gap Type: {gap_type}
        Technical Audit Results: {'; '.join(deep_audit_results)}
        Tool-Suggested Actions: {', '.join(tool_actions)}
        Root Cause: {root_cause_report.root_cause}
        Raw Data: {json.dumps(signal.raw_data, indent=2)}
        """
        
        # Use the RLM client to process the incident brief
        state = await self.rlm_client.process(incident_brief, preset="medium")
        final_synthesis = state.get("final_result", "")
        
        # Check for RLM Error
        is_rlm_error = "RLM Failure" in final_synthesis or "API Key Missing" in final_synthesis or "RLM JSON decoding failure" in final_synthesis or "error" in final_synthesis.lower()

        if is_rlm_error or not final_synthesis.strip():
            recommended_tests = tool_actions[:2]
            recommended_monitoring = ["Add automated monitoring for signal type: " + signal.signal_type]
        else:
            recommended_tests = [f"[RLM Synthesis]: {final_synthesis[:200]}..."]
            recommended_monitoring = [f"Monitor {root_cause_report.affected_capability} for similar patterns identified by RLM."]

        print(f"[DataGapAgent]: Data gaps identified for {signal.signal_id}.")

        return PreventionPlan(
            signal_id=signal.signal_id,
            missing_data_quality_tests=recommended_tests,
            monitoring_gaps=recommended_monitoring
        )
