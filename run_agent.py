import sys
import os
import json
from google import genai
from dotenv import load_dotenv

# Bulletproof path injection to find the backend components
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
backend_path = os.path.join(root_dir, 'Magellan-rca-engine-backend')
sys.path.insert(0, backend_path)

from app.schemas.shared_ingress import IncomingSignal
from app.services.context.anomaly_detector import AnomalyDetector
from app.services.context.mxp_context import MXPContextBuilder
from app.agents.experts.mxp_rules_agent import MXPRulesAgent

def run_pipeline():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY is missing from your .env file.")
        return

    # 1. RUN DETECTOR (Automated Phase 1 scanning your mock data)
    print("⚡ [Phase 1] Scanning mock data for MXP rules and stock alignment anomalies...")
    detector = AnomalyDetector(
        logs_filepath="./mock_data/search_events.jsonl",
        rules_filepath="./mock_data/rules.json"
    )
    anomalies = detector.scan_for_anomalies()
    
    # Save the detected anomalies file directly to project root
    with open("anomalies.json", "w") as f:
        json.dump(anomalies, f, indent=2)
    print(f"💾 Found {len(anomalies)} critical anomaly. Saved details to anomalies.json")

    # 2. RUN RCA ENGINE (Phase 2 processing discovered errors)
    builder = MXPContextBuilder(
        rules_filepath="./mock_data/rules.json",
        logs_filepath="./mock_data/search_events.jsonl"
    )
    client = genai.Client(api_key=api_key)
    agent = MXPRulesAgent(context_builder=builder, gemini_client=client)

    print("\n🕵️‍♂️ [Phase 2] Executing Root Cause Analysis Engine...")
    for entry in anomalies:
        signal = IncomingSignal(
            signal_id=entry["signal_id"],
            anomaly_type=entry["anomaly_type"],
            query_text=entry["query_text"],
            impacted_product_id=entry["impacted_product_id"],
            current_metric_value=entry["current_metric_value"]
        )
        # Attach the metadata dict dynamically back to the signal object
        signal.metadata = entry.get("metadata", {})

        # Generate Evidence Pack via Gemini Pro
        evidence_pack = agent.analyze(signal)
        
        print("\n================ FINAL DELIVERABLE: THE EVIDENCE PACK ================\n")
        print(evidence_pack.model_dump_json(indent=2))
        print("\n======================================================================\n")

if __name__ == "__main__":
    run_pipeline()