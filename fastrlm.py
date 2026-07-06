#!/usr/bin/env python3
import os
import sys
import json
import tempfile
import shutil
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

# Load environment variables and configure fast-rlm
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY is missing from .env")
    sys.exit(1)
os.environ["RLM_MODEL_API_KEY"] = api_key
os.environ["RLM_MODEL_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/"

import fast_rlm

# =========================
# OUTPUT SCHEMA MODEL
# =========================

class AgentOutput(BaseModel):
    """Structured Root Cause Analysis Report from fast-rlm."""
    overall_status: str = Field(..., description="'SUCCESS' or 'FAILED'.")
    root_cause: str = Field(..., description="Precise failure logic statement.")
    affected_capabilities: List[str] = Field(..., description="List of business capabilities impacted.")
    summary: str = Field(..., description="Brief narrative summarizing findings.")
    detailed_evidence: List[str] = Field(..., description="Supporting evidence points from tools.")

# =================================
# DYNAMIC TOOL MODULE GENERATOR
# =================================

def create_tool_module(rules_data_str: str, logs_data_str: str, temp_dir: str):
    """Dynamically generates and imports a tool module with data injected into source."""
    rules_escaped = json.dumps(rules_data_str)
    logs_escaped = json.dumps(logs_data_str)

    tool_source = f'''
import json

def get_rule_metadata(rule_id: str) -> str:
    """Fetches configuration of an MXP rule by its ID."""
    rules_data = json.loads({rules_escaped})
    rules = rules_data.get("rules", [])
    for rule in rules:
        if isinstance(rule, dict) and rule.get("rule_id") == rule_id:
            return json.dumps(rule, indent=2)
    return f"Rule {{rule_id}} not found."

def get_inventory_status(product_id: str) -> str:
    """Checks stock levels and data quality for a product_id."""
    import json
    rules_data = json.loads({rules_escaped})
    rules = rules_data.get("rules", [])
    for rule in rules:
        if not isinstance(rule, dict): continue
        for snap in rule.get("target_product_snapshots", []):
            if isinstance(snap, dict) and snap.get("id") == product_id:
                return json.dumps(snap, indent=2)
    return f"Product {{product_id}} snapshot not found."

def get_traffic_metrics(product_id: str) -> str:
    """Pulls impressions, clicks, and CTR for a product_id from search logs."""
    import json
    logs_data_str = {logs_escaped}
    impressions, clicks = 0, 0
    for line in logs_data_str.strip().split('\\n'):
        if not line.strip(): continue
        event = json.loads(line)
        for res in event.get("response", {{}}).get("results", []):
            pid = res.get("product_id") if isinstance(res, dict) else res
            if pid == product_id: impressions += 1
        for click in event.get("interaction", {{}}).get("clicks", []):
            pid = click.get("product_id") if isinstance(click, dict) else click
            if pid == product_id: clicks += 1
    ctr = (clicks / impressions) * 100 if impressions > 0 else 0.0
    return f"Traffic for {{product_id}}: impressions={{impressions}}, clicks={{clicks}}, CTR={{ctr:.2f}}%"
'''
    
    with open(os.path.join(temp_dir, "fast_rlm_tools.py"), "w") as f:
        f.write(tool_source)
    sys.path.insert(0, temp_dir)
    import fast_rlm_tools
    return [fast_rlm_tools.get_rule_metadata, fast_rlm_tools.get_inventory_status, fast_rlm_tools.get_traffic_metrics]

# =========================
# MAIN EXECUTION PIPELINE
# =========================

def main():
    temp_dir = tempfile.mkdtemp(prefix="fastrlm_tools_")
    try:
        # Load data into memory
        with open("mock_data/rules.json", "r") as f: rules_data_str = f.read()
        with open("mock_data/search_events.jsonl", "r") as f: logs_data_str = f.read()
        with open("anomalies.json", "r") as f: anomalies = json.load(f)

        print(f"🕵️‍♂️ Found {len(anomalies)} anomalies. Starting fast-rlm RCA diagnostics...\n")
        
        # Create and import the data-injected tools from the temporary module
        tools = create_tool_module(rules_data_str, logs_data_str, temp_dir)

        # Process first 3 anomalies for a rapid demo
        for idx, anomaly in enumerate(anomalies[:3], start=1):
            signal_id = anomaly.get("signal_id", f"SIG-UNKNOWN-{idx}")
            rule_id = anomaly.get("metadata", {}).get("suspected_rule_id", "UNKNOWN")
            product_id = anomaly.get("impacted_product_id", "UNKNOWN")
            
            print(f"──────────────────────────────────────────────────────────────────────")
            print(f"🔍 [FAST-RLM] Investigating {signal_id} (Rule: {rule_id}, Product: {product_id})")
            print(f"──────────────────────────────────────────────────────────────────────")

            query_str = f'''
Anomaly Signal Payload: {json.dumps(anomaly, indent=2)}

Perform a thorough Root Cause Analysis (RCA).
Instructions:
1. Verify rule config for '{rule_id}' using 'get_rule_metadata'.
2. Check inventory for '{product_id}' using 'get_inventory_status'.
3. Examine traffic for '{product_id}' using 'get_traffic_metrics'.
State the exact root cause and supporting evidence, conforming to the AgentOutput schema.
'''
            
            try:
                response = fast_rlm.run(
                    query=query_str,
                    config={"primary_agent": "gemini-2.5-flash"},
                    output_schema=AgentOutput,
                    tools=tools,
                    verbosity=1
                )
                
                print("\n[ RCA Deliverable for Anomaly ]")
                print(json.dumps(response["results"], indent=2))
                print()
                
            except Exception as e:
                print(f"❌ Failed to diagnose {signal_id}: {e}\n")

    finally:
        # Clean up the temporary directory and module
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
