# Runbook_System_Final/agents/suggest_tuning/core.py
"""Agent to handle OCSS Suggest Service tuning and prefix clustering."""
import json
import logging
from typing import List, Dict, Any
from Runbook_System_Final.shared.schemas import OpsSignal, RootCauseReport, SuggestTuningReport
from Runbook_System_Final.orchestration.rlm_client import RLMClient

logger = logging.getLogger(__name__)

class SuggestTuningAgent:
    """
    The SuggestTuningAgent identifies patterns in failed prefixes and queries,
    mines the catalog for potential matches, and generates tuning packs
    for the Suggest Service and Querqy using RLM for synthesis.
    """
    def __init__(self, rlm_client: RLMClient):
        self.rlm_client = rlm_client
        logger.info("SuggestTuningAgent initialized with RLMClient.")

    async def run(self, signal: OpsSignal, root_cause: RootCauseReport) -> SuggestTuningReport:
        """
        Analyzes the signal to generate a suggestion tuning pack.
        """
        logger.info(f"Running SuggestTuningAgent for signal {signal.signal_id}")

        analysis_prompt = f"""
        Task: Cluster failed search prefixes and generate a Suggestion Tuning Pack for OCSS Suggest Service.
        
        Incident Signal: {signal.summary}
        Root Cause: {root_cause.root_cause}
        Affected Capability: {root_cause.affected_capability}
        
        Raw Data (Query Logs/Prefixes):
        {json.dumps(signal.raw_data, indent=2)}
        
        Instructions:
        1. Cluster any failed prefixes or typos found in the raw data into logical groups.
        2. Mine the catalog context provided in raw data to find relevant replacement terms or synonyms.
        3. Generate a 'Suggest Pack' JSON structure with 'term', 'suggestion', and 'confidence'.
        4. Estimate the CTR lift (as a float, e.g. 0.12 for 12%) if these suggestions were active.
        5. Provide a business impact summary.
        
        Return the result as a structured JSON object with the following keys:
        - failed_prefix_clusters: List of objects with 'cluster_id', 'members', 'count'
        - suggest_pack: List of objects with 'term', 'suggestion', 'confidence'
        - estimated_ctr_lift: float
        - business_impact_summary: string
        """

        state = await self.rlm_client.process(analysis_prompt, preset="high")
        synthesis = state.get("final_result", "{}")

        # Try to parse the LLM response as JSON
        try:
            if "```json" in synthesis:
                synthesis = synthesis.split("```json")[1].split("```")[0].strip()
            elif "{" in synthesis and "}" in synthesis:
                 start = synthesis.find("{")
                 end = synthesis.rfind("}") + 1
                 synthesis = synthesis[start:end]
            
            tuning_data = json.loads(synthesis)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM output as JSON. Using fallback. Error: {e}")
            tuning_data = self._generate_fallback_data(signal)

        return SuggestTuningReport(
            signal_id=signal.signal_id,
            failed_prefix_clusters=tuning_data.get("failed_prefix_clusters", []),
            suggest_pack=tuning_data.get("suggest_pack", []),
            estimated_ctr_lift=tuning_data.get("estimated_ctr_lift", 0.05),
            business_impact_summary=tuning_data.get("business_impact_summary", "Manual review required for demand trend.")
        )

    def _generate_fallback_data(self, signal: OpsSignal) -> Dict[str, Any]:
        """Fallback logic if RLM synthesis fails."""
        query = signal.raw_data.get("query", "unknown")
        return {
            "failed_prefix_clusters": [
                {"cluster_id": "unknown_demand", "members": [query[:3], query[:5]] if len(query) > 5 else [query], "count": 1}
            ],
            "suggest_pack": [
                {"term": query, "suggestion": "trending_products", "confidence": 0.5}
            ],
            "estimated_ctr_lift": 0.02,
            "business_impact_summary": f"Detected failed prefix for '{query}'. Proposing generic trending fallback."
        }
