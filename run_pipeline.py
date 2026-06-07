# Runbook_System_Final/run_pipeline.py
"""
A simple script to run the full runbook pipeline from a sample file.
"""
import sys
import os
from pathlib import Path

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

from orchestration.orchestrator import run_from_file
import pprint


def main():
    """
    Main entry point for running the agent pipeline.
    """
    # Use the specific Magellan Scenario A (Catalog Gap)
    input_file = CURRENT_DIR / "samples" / "magellan_scenario_a_catalog.json"
    
    if not input_file.exists():
        print(f"❌ Error: Input file not found at {input_file}")
        return

    print(f"Running pipeline with input file: {input_file.name}")
    
    try:
        # Execute the entire agent pipeline
        # run_from_file expects a path string
        final_runbook = run_from_file(str(input_file))
        
        # The orchestrator provides a beautiful trace, so we don't need to print everything here
        
    except Exception as e:
        print(f"\n❌ PIPELINE EXECUTION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
