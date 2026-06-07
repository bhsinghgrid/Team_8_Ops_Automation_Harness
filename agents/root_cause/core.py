# Runbook_System_Final/agents/root_cause/core.py
"""Agent to determine the root cause of an operational signal."""
import json
from typing import Dict, Any
from shared.schemas import OpsSignal, RootCauseReport
from orchestration import RLMClient

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

        incident_brief = f"""
        Task: Decompose this operational signal, analyze the symptom, and compose a final root cause and affected capability.
        Signal Type: {signal.signal_type}
        Summary: {signal.summary}
        Evidence: {json.dumps(signal.raw_data, indent=2)}
        """

        # Use the RLM client to process the incident brief
        state = await self.rlm_client.process(incident_brief, preset="medium")
        final_synthesis = state.get("final_result", "")
        
        # Mapping logic (Deterministic or RLM-based)
        # This logic could also be enhanced by the RLM itself if needed.
        if "stale_embedding" in signal.signal_type:
            capability = "Stale Embeddings"
        elif "vocabulary" in signal.signal_type or "autocomplete" in signal.signal_type:
            capability = "Smart Autocomplete"
        elif "low_result" in signal.signal_type:
            capability = "Semantic Retrieval"
        elif "catalog" in signal.signal_type:
            capability = "Catalog Optimization"
        elif "mismatch" in signal.signal_type:
            capability = "Infrastructure (Vector DB)"
        elif "conflict" in signal.signal_type:
            capability = "MXP Merchandising"
        else:
            capability = "Search API Handling"

        print(f"[RootCauseAgent]: Root cause identified for {signal.signal_id}. Affected capability: {capability}")

        return RootCauseReport(
            signal_id=signal.signal_id,
            root_cause=f"[RLM Synthesized Output]: {final_synthesis[:200]}...", # Truncate for brevity
            affected_capability=capability,
            evidence=[
                f"raw_signal_{signal.signal_id}.json",
                f"RLM Subtasks Decomposed: {len(state.get('decomposed_tasks', []))}",
                f"RLM Cache Hits: {state.get('cache_hits', 0)}",
                f"RLM Self-Critique Retries: {state.get('retry_count', 0)}"
            ]
        )
