#!/bin/bash
source ./MagellanFrontend/.venv/bin/activate

echo "--- Waiting for Temporal Server ---" 
python3 temporal/wait_for_server.py

echo "--- Starting Temporal Worker ---"
python3 temporal/run_worker.py > worker_log.txt 2>&1
deactivate
