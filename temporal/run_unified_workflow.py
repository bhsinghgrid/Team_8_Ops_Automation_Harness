import asyncio
import time
import json
import sys
from temporalio.client import Client

# To ensure the parent directory is in the Python path for module resolution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from  temporal.workflows import UnifiedSearchAiRepairWorkflow

import httpx

async def main():
    # Adding a small delay to allow the server to be fully ready
    await asyncio.sleep(2)
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    print(f"Connecting to Temporal server at {temporal_address}...")
    client = await Client.connect(temporal_address)
    print("✅ Temporal client connected")

    # Determine the workflow type from the command-line argument, defaulting to 'catalog'
    valid_types = ["catalog", "autocomplete", "semantic"]
    signal_type = "catalog" # Default
    if len(sys.argv) > 1 and sys.argv[1] in valid_types:
        signal_type = sys.argv[1]

    print(f"Preparing to run a '{signal_type}' workflow.")

    # Create a relevant, focused, and small signal based on the workflow type
    if signal_type == "catalog":
        print("Loading targeted anomalies for the Catalog agent.")
        try:
            with open("Catalog/catalog_anomalies.jsonl", "r") as f:
                anomalous_events = [json.loads(line) for line in f]
            
            initial_signal = {
                "description": f"ALERT: Search quality degradation test run. Processing a targeted batch of {len(anomalous_events)} anomalous events.",
                "events": anomalous_events,
            }
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading or parsing catalog_anomalies.jsonl: {e}. Using a fallback signal.")
            initial_signal = {
                "description": "Fallback signal for catalog health check.",
                "events": [{"issue": "catalog_health_check", "severity": "low"}],
            }

    elif signal_type == "autocomplete":
        print("Loading targeted anomalies for the Autocomplete agent.")
        try:
            with open("Autocomplete/autocomplete_anomalies.jsonl", "r") as f:
                anomalous_events = [json.loads(line) for line in f]
            
            initial_signal = {
                "description": f"ALERT: Autocomplete quality degradation test run. Processing a targeted batch of {len(anomalous_events)} anomalous events.",
                "events": anomalous_events,
            }
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading or parsing autocomplete_anomalies.jsonl: {e}. Using a fallback signal.")
            initial_signal = {
                "description": "Fallback signal for autocomplete health check.",
                "events": [{"issue": "autocomplete_health_check", "severity": "low"}],
            }

    elif signal_type == "semantic":
        print("Loading targeted anomalies for the Semantic agent.")
        try:
            with open("Semantic/semantic_anomalies.jsonl", "r") as f:
                anomalous_events = [json.loads(line) for line in f]
            
            initial_signal = {
                "description": f"ALERT: Semantic search quality degradation test run. Processing a targeted batch of {len(anomalous_events)} anomalous events.",
                "events": anomalous_events,
            }
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading or parsing semantic_anomalies.jsonl: {e}. Using a fallback signal.")
            initial_signal = {
                "description": "Fallback signal for semantic health check.",
                "events": [{"issue": "semantic_health_check", "severity": "low"}],
            }
    
    initial_signal["type"] = signal_type

    workflow_id = f"unified-search-repair-workflow-{int(time.time())}"

    print(f"Executing Unified Search AI Repair Workflow with ID: {workflow_id}")
    print(f"Signal Type: {initial_signal['type']}")
    print(f"Initial signal being sent to workflow: {json.dumps(initial_signal, indent=2)}")
    
    handle = await client.start_workflow(
        UnifiedSearchAiRepairWorkflow.run,
        initial_signal,
        id=workflow_id,
        task_queue="search-ai-task-queue",
    )
    print(f"✅ Workflow '{handle.id}' started")

    result = await handle.result()
    print("\nWorkflow completed. Final Release Result:")
    print(result)

    # --- NEW: Report the results back to the FastAPI backend ---
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                "http://localhost:8000/api/runbooks/complete-run",
                json={"workflow_id": handle.id, "result": result},
                timeout=10,
            )
            response.raise_for_status()
            print("✅ Successfully reported results to the backend.")
    except httpx.RequestError as e:
        print(f"❌ Failed to report results to backend: {e}")


if __name__ == "__main__":
    asyncio.run(main())
