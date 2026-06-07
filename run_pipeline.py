# Runbook_System_Final/run_pipeline.py
"""
A simple script to run the full runbook pipeline from a sample file.
"""
import sys
import os
from pathlib import Path
import json
import uuid

# Add the current directory and all its submodules to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT = CURRENT_DIR.parent
SRC_DIR = ROOT / "src"

paths_to_add = [
    str(CURRENT_DIR),
    str(CURRENT_DIR / "agents"),
    str(CURRENT_DIR / "brain"),
    str(CURRENT_DIR / "shared"),
    str(CURRENT_DIR / "tools"),
    str(SRC_DIR),
    str(ROOT)
]

for p in paths_to_add:
    if p not in sys.path:
        sys.path.insert(0, p)

from orchestration.orchestrator import run_from_file, execute_pipeline
import pprint
import asyncio


async def main():
    """
    Main entry point for running the agent pipeline.
    """
    # Use the specific Magellan Scenario A (Catalog Gap)
    input_file = ROOT / "Magellan-signal-ingestion-backend" / "mock-data" / "scenarios" / "catalog_scenarios.json"
    
    if not input_file.exists():
        print(f"❌ Error: Input file not found at {input_file}")
        return

    print(f"Running pipeline with input file: {input_file.name}")
    
    try:
        # Load the scenarios file
        with open(input_file, 'r') as f:
            scenarios_data = json.load(f)
        
        # Take the first scenario and format it to match the expected 'signal_data' structure
        if "scenarios" not in scenarios_data or not scenarios_data["scenarios"]:
            print(f"❌ Error: No scenarios found in {input_file}")
            return

        first_scenario = scenarios_data["scenarios"][0]
        
        # Construct a synthetic signal_data that orchestrator expects
        synthetic_signal_data = {
            "signals": [
                {
                    "id": f"scenario-{first_scenario.get('product_id', 'unknown')}-{uuid.uuid4().hex[:8]}", # Generate a unique ID
                    "type": f"catalog_{first_scenario.get('operation', 'unknown').lower()}",
                    "summary": first_scenario.get('name', 'No summary provided'),
                    "raw_data": first_scenario # Pass the entire scenario as raw_data
                }
            ]
        }
        
        # Execute the entire agent pipeline with the synthetic signal_data
        final_runbook = await execute_pipeline(synthetic_signal_data)
        
        # The orchestrator provides a beautiful trace, so we don\'t need to print everything here
        
    except Exception as e:
        print(f"\n❌ PIPELINE EXECUTION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
