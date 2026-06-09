# Runbook_System_Final/agents/root_cause/core.py
"""Agent to determine the root cause of an operational signal."""
import json
from typing import Dict, Any
from Runbook_System_Final.shared.schemas import OpsSignal, RootCauseReport
from Runbook_System_Final.orchestration.rlm_client import RLMClient
from Runbook_System_Final.tools import capability_mapping_tools, signal_tools

class RootCauseAgent:
    """
    The RootCauseAgent identifies the underlying cause and affected capability
    based on an operational signal using the RLM.
    """
    def __init__(self, rlm_client: RLMClient):
        self.rlm_client = rlm_client
        print("[RootCauseAgent]: Initialized with RLMClient.")

    async def run(self, signal: OpsSignal) -> RootCauseReport:
        """Analyzes an ops signal using the Recursive Language Model (RLM)."""
        print(f"[RootCauseAgent]: Analyzing signal {signal.signal_id} for root cause...")

        # 1. Use existing tools to infer capability and collect signals
        inferred_capability = capability_mapping_tools.infer_capability_from_signal(signal.raw_data)
        capability_family = capability_mapping_tools.capability_family(signal.signal_type, inferred_capability)
        
        incident_brief = f"""
        Task: Decompose this operational signal, analyze the symptom, and compose a final root cause.
        Inferred Capability: {inferred_capability} ({capability_family})
        Signal Type: {signal.signal_type}
        Summary: {signal.summary}
        Evidence: {json.dumps(signal.raw_data, indent=2)}
        """

        # Use the RLM client to process the incident brief
        state = await self.rlm_client.process(incident_brief, preset="medium")
        final_synthesis = state.get("final_result", "")
        
        # Check for RLM Error
        if isinstance(final_synthesis, dict):
            is_rlm_error = (
                final_synthesis.get("status") == "error"
                or final_synthesis.get("error") is not None
            )
        else:
            is_rlm_error = "error" in str(final_synthesis).lower()

        # Mapping logic (Hybrid: Tool-based with RLM enrichment)
        capability = inferred_capability.replace("_", " ").title() if inferred_capability != "unknown" else "Search API Handling"
        fallback_root_cause = f"Detected issue in {capability} based on signal type {signal.signal_type}."

        if is_rlm_error or not str(final_synthesis).strip():
            # Enhanced Error Handling: Fallback to deterministic rules when AI is unavailable
            root_cause_desc = f"[Fallback Rule Applied due to AI Error]: {fallback_root_cause}"
            evidence_details = [
                f"raw_signal_{signal.signal_id}.json",
                f"Warning: AI Model Unavailable or returned an error. Relying on deterministic rules.",
            ]
            
            # Enrich fallback evidence from raw data
            raw_evidence = signal.raw_data.get("evidence", [])
            for e in raw_evidence:
                evidence_details.append(f"Extracted Evidence: {e.get('field', 'Unknown Field')} - {e.get('message', '')}")
                
        else:
            # Use successful RLM synthesis
            root_cause_desc = f"[RLM Synthesized Output]: {str(final_synthesis)[:500]}..." # Increased length for better context
            evidence_details = [
                f"raw_signal_{signal.signal_id}.json",
                f"RLM Subtasks Decomposed: {len(state.get('decomposed_tasks', []))}",
                f"RLM Cache Hits: {state.get('cache_hits', 0)}",
                f"RLM Self-Critique Retries: {state.get('retry_count', 0)}"
            ]

        print(f"[RootCauseAgent]: Root cause identified for {signal.signal_id}. Affected capability: {capability}")

        return RootCauseReport(
            signal_id=signal.signal_id,
            root_cause=root_cause_desc,
            affected_capability=capability,
            evidence=evidence_details
        )
