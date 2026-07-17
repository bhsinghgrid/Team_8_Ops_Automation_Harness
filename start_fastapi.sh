#!/bin/bash
set -x
source ./MagellanFrontend/.venv/bin/activate

# Set the correct task queue for the backend to use
export TEMPORAL_TASK_QUEUE="search-ai-task-queue"

# lsof -t -i :8000 | xargs -r kill -9 || true
uvicorn MagellanFrontend.fastapi_app:app --host 0.0.0.0 --port 8000
deactivate
