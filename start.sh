#!/bin/bash
set -m # Enable Job Control

# Activate the virtual environment
# The Dockerfile installs dependencies globally, so this is not strictly needed
# but is good practice if you adapt this script for non-container use.
# source .venv/bin/activate

# Start the Temporal worker in the background
echo "--- Starting Temporal Worker ---"
python3 temporal/run_worker.py &

# Start the FastAPI backend in the foreground
echo "--- Starting FastAPI Server on port 8000 ---"
uvicorn MagellanFrontend.backend_app.app:app --host 0.0.0.0 --port 8000

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
