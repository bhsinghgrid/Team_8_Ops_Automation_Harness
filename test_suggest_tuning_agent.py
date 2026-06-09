# test_suggest_tuning_agent.py
import asyncio
import os
import sys
from pathlib import Path

# Add workspace root to sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Runbook_System_Final.agents.suggest_tuning.core import SuggestTuningAgent
from Runbook_System_Final.shared.schemas import OpsSignal, RootCauseReport
from Runbook_System_Final.orchestration.rlm_client import RLMClient

async def test_agent():
    print("🚀 Testing SuggestTuningAgent...")
    
    # Initialize RLM Client (ensure GOOGLE_API_KEY is set in environment)
    rlm = RLMClient()
    agent = SuggestTuningAgent(rlm)
    
    # Mock Signal: Demand Trend for "waterproof trail shoes"
    signal = OpsSignal(
        signal_id="sig-suggest-001",
        signal_type="autocomplete_miss",
        summary="Rising zero-completion prefixes for trail shoes.",
        raw_data={
            "query": "waterproof trail shoes",
            "failed_prefixes": ["wat", "waterp", "waterpro", "trail s", "trail sh"],
            "catalog_context": {
                "relevant_tags": ["water-resistant", "hiking", "outdoor", "gore-tex"],
                "top_products": ["Hiking Boot Alpha", "Trail Runner X"]
            }
        }
    )
    
    # Mock Root Cause
    root_cause = RootCauseReport(
        signal_id="sig-suggest-001",
        root_cause="Suggest Service missing vocabulary for seasonal outdoor footwear.",
        affected_capability="OCSS Suggest Service",
        evidence=["query_logs_june.csv"]
    )
    
    # Run Agent
    report = await agent.run(signal, root_cause)
    
    print("\n--- Suggest Tuning Report ---")
    print(f"Signal ID: {report.signal_id}")
    print(f"Estimated CTR Lift: {report.estimated_ctr_lift * 100}%")
    print(f"Business Impact: {report.business_impact_summary}")
    print("\nFailed Prefix Clusters:")
    for cluster in report.failed_prefix_clusters:
        print(f" - {cluster.get('cluster_id')}: {cluster.get('members')} ({cluster.get('count')})")
    
    print("\nSuggest Pack Candidates:")
    for item in report.suggest_pack:
        print(f" - Term: {item.get('term')} -> Suggestion: {item.get('suggestion')} (Conf: {item.get('confidence')})")

if __name__ == "__main__":
    # Ensure you have your API key set
    if not os.environ.get("GOOGLE_API_KEY"):
        print("⚠️ Warning: GOOGLE_API_KEY not found. Agent will use fallback logic.")
    
    asyncio.run(test_agent())
