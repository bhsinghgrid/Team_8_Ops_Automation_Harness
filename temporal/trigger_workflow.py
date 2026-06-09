# temporal/trigger_workflow.py
import asyncio
import sys
from pathlib import Path
import uuid

# Set up path to find the temporal module
CURRENT_DIR = Path(__file__).resolve().parent
ROOT = CURRENT_DIR.parent
paths_to_add = [
    str(ROOT),
    str(ROOT / "Runbook_System_Final"),
]
for p in paths_to_add:
    if p not in sys.path:
        sys.path.insert(0, p)

from temporalio.client import Client
from temporal.workflows import SignalToRunbookWorkflow

async def main():
    """
    This script starts the main parent workflow for the entire Signal-to-Runbook process.
    """
    print("🚀 Initiating the main Signal-to-Runbook parent workflow...")
    
    client = await Client.connect("localhost:7233")

    # This starts the parent workflow and returns immediately.
    # The workflow will continue to run in the background.
    handle = await client.start_workflow(
        SignalToRunbookWorkflow.execute,
        "Elasticsearch Manual Trigger", # This will now show up in the Temporal UI 'Input'
        id=f"signal-to-runbook-parent-workflow-{uuid.uuid4()}",
        task_queue="magellan-runbook-execution-task-queue",
    )

    print(f"\n✅ Workflow started successfully!")
    print(f"   Workflow ID: {handle.id}")
    print(f"   Run ID: {handle.first_execution_run_id}")
    print("\n✨ You can now monitor its progress in the Temporal Web UI.")

if __name__ == "__main__":
    asyncio.run(main())
