# temporal/worker.py
"""
Temporal Worker for the Magellan Runbook Execution Pipeline.
This worker connects to the Temporal server and runs workflows/activities.
"""
import asyncio
import sys
import os
from temporalio.worker import Worker
from temporalio.client import Client
from prometheus_client import start_http_server

# Add the workspace root to sys.path to allow imports from all sub-projects
if str(os.getcwd()) not in sys.path:
    sys.path.insert(0, str(os.getcwd()))

# Import workflows and the consolidated activities module
from temporal.workflows import FullPipelineWorkflow, SignalToRunbookWorkflow
import temporal.all_activities

# Main entry point for the worker
async def main():
    # Start Prometheus telemetry server on port 8001 for P95 tracking
    # (Port 8000 is used by the Magellan backend)
    print("📊 Starting Prometheus metrics server on port 8001...")
    start_http_server(8001)

    # Connect to Temporal server
    client = await Client.connect("localhost:7233")
    
    # Create a worker that will listen for tasks on specific queues
    worker = Worker(
        client,
        task_queue="magellan-runbook-execution-task-queue",
        workflows=[FullPipelineWorkflow, SignalToRunbookWorkflow],
        activities=temporal.all_activities.ALL_ACTIVITIES, # Register all activities from the consolidated file
    )
    print("✅ Temporal Worker started, listening on task queue: 'magellan-runbook-execution-task-queue'")
    print("   Registered Workflows: [FullPipelineWorkflow, SignalToRunbookWorkflow]")
    print(f"  Registered Activities: {len(temporal.all_activities.ALL_ACTIVITIES)} total")
    
    # Start the worker. It will run forever until interrupted.
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
