# temporal/feedback_worker.py
import asyncio
import sys
import os
from pathlib import Path
from temporalio.worker import Worker
from temporalio.client import Client
from prometheus_client import start_http_server

# Add workspace root and Feedback folder to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))
if str(WORKSPACE_ROOT / "Feedback") not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT / "Feedback"))

# Import original activities and workflows
import temporal.all_activities
from temporal.workflows import FullPipelineWorkflow, SignalToRunbookWorkflow

# Import new activities and workflows
from temporal.feedback_activities import run_feedback_agent_activity, run_canary_rollout_activity
from temporal.feedback_workflows import IntegratedFeedbackWorkflow, IntegratedSignalToRunbookWorkflow

# Combine activities
INTEGRATED_ACTIVITIES = temporal.all_activities.ALL_ACTIVITIES + [
    run_feedback_agent_activity,
    run_canary_rollout_activity
]

async def main():
    print("📊 Starting Prometheus metrics server on port 8002...")
    try:
        start_http_server(8002)
    except Exception:
        print("Prometheus server already running or port 8002 occupied.")

    client = await Client.connect("localhost:7233")
    
    worker = Worker(
        client,
        task_queue="magellan-runbook-execution-task-queue",
        workflows=[
            FullPipelineWorkflow, 
            SignalToRunbookWorkflow,
            IntegratedFeedbackWorkflow,
            IntegratedSignalToRunbookWorkflow
        ],
        activities=INTEGRATED_ACTIVITIES,
    )
    print("✅ Integrated Feedback Worker started")
    print(f"   Registered Activities: {len(INTEGRATED_ACTIVITIES)}")
    
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
