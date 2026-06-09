# temporal/trigger_feedback_workflow.py
import asyncio
import sys
from pathlib import Path
import uuid

CURRENT_DIR = Path(__file__).resolve().parent
ROOT = CURRENT_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from temporalio.client import Client
from temporal.feedback_workflows import IntegratedSignalToRunbookWorkflow

async def main():
    print("🚀 Initiating the Integrated Feedback Workflow...")
    
    client = await Client.connect("localhost:7233")

    handle = await client.start_workflow(
        IntegratedSignalToRunbookWorkflow.execute,
        "Feedback Layer Integration Test",
        id=f"integrated-feedback-workflow-{uuid.uuid4()}",
        task_queue="magellan-runbook-execution-task-queue",
    )

    print(f"\n✅ Workflow started successfully!")
    print(f"   Workflow ID: {handle.id}")
    print("\n✨ You can now monitor its progress in the Temporal Web UI.")

if __name__ == "__main__":
    asyncio.run(main())
