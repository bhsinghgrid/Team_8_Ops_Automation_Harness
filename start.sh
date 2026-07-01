#!/bin/bash
set -m # Enable Job Control

# Activate the virtual environment (for local development/testing outside Docker)
source MagellanFrontend/.venv/bin/activate

# NOTE: Dependency installation and PYTHONPATH setup are handled by Dockerfile for containerized deployment.
# The following sections are commented out as they are now handled by Docker.
# export PYTHONPATH=$PYTHONPATH:/Users/bhsingh/Documents/Magellan_Harness/shadow_agent/src
# echo "--- Installing main project requirements ---"
# MagellanFrontend/.venv/bin/pip install -r requirements.txt
# echo "--- Installing shadow_agent ---"
# MagellanFrontend/.venv/bin/pip install -e /Users/bhsingh/Documents/Magellan_Harness/shadow_agent

# Start the Temporal worker in the background
echo "--- Waiting for Temporal Server ---"
MagellanFrontend/.venv/bin/python3 temporal/wait_for_server.py

echo "--- Starting Temporal Worker ---"
MagellanFrontend/.venv/bin/python3 temporal/run_worker.py &

# Start the FastAPI backend in the foreground
echo "--- Starting FastAPI Server on port 8000 ---"
lsof -t -i :8000 | xargs -r kill -9 || true
uvicorn MagellanFrontend.backend_app.app:app --host 0.0.0.0 --port 8000 &

# Run the Unified Temporal Workflow client
echo "--- Running Unified Temporal Workflow ---"
MagellanFrontend/.venv/bin/python3 temporal/run_unified_workflow.py

# Wait for any process to exit
wait

# Exit with status of process that exited first
exit $?

