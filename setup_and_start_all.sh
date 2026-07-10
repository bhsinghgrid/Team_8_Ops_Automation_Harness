#!/bin/bash
# ==============================================================================
# 🚀 Autonomous Ops Harness - Local Multi-Environment Setup & Startup Orchestrator
# ==============================================================================
# This script sequentially activates the local virtual environments for each 
# sub-project folder, installs/updates dependencies, and boots the background 
# services (Temporal Workers, FastAPI Backend, React Frontend, Feedback Agent).
# ==============================================================================

set -m # Enable Job Control to manage multiple background processes

echo "=========================================================================="
echo "📦 STEP 1: INITIALIZING & UPDATING LOCAL ENVIRONMENTS"
echo "=========================================================================="

# --- 1. Root Workspace Environment (.venv) ---
echo "--- 🔄 Activating Root Workspace Virtual Environment ---"
if [ -f "./.venv/bin/activate" ]; then
    source ./.venv/bin/activate
    echo "✅ Root Virtual Environment Activated."
    echo "--- Installing Root Requirements ---"
    ./.venv/bin/pip install --no-cache-dir -r requirements.txt
    deactivate
else
    echo "⚠️ Warning: Root .venv not found at ./.venv. Skipping."
fi

# --- 2. Frontend / API Web-Console Environment (MagellanFrontend/.venv) ---
echo -e "\n--- 🔄 Activating MagellanFrontend Virtual Environment ---"
if [ -f "./MagellanFrontend/.venv/bin/activate" ]; then
    source ./MagellanFrontend/.venv/bin/activate
    echo "✅ MagellanFrontend Virtual Environment Activated."
    echo "--- Installing Frontend Requirements ---"
    if [ -f "./MagellanFrontend/requirements.txt" ]; then
        ./MagellanFrontend/.venv/bin/pip install --no-cache-dir -r ./MagellanFrontend/requirements.txt
    else
        # Fallback to root requirements if not present in folder
        ./MagellanFrontend/.venv/bin/pip install --no-cache-dir -r requirements.txt
    fi
    deactivate
else
    echo "⚠️ Warning: MagellanFrontend .venv not found at ./MagellanFrontend/.venv. Skipping."
fi

# --- 3. Feedback Agent Environment (feedback_agent/ if applicable) ---
# If feedback_agent has its own requirements, let's establish its dependencies using root .venv as fallback
echo -e "\n--- 🔄 Setting up Feedback Agent Dependencies ---"
if [ -d "./feedback_agent" ] && [ -f "./feedback_agent/requirements.txt" ]; then
    if [ -f "./.venv/bin/activate" ]; then
        source ./.venv/bin/activate
        echo "✅ Activated Root Environment to install Feedback Agent requirements."
        ./.venv/bin/pip install --no-cache-dir -r ./feedback_agent/requirements.txt
        deactivate
    else
         echo "⚠️ Warning: Could not install Feedback Agent dependencies (No active virtual environment)."
    fi
fi

echo -e "\n=========================================================================="
echo "⚡ STEP 2: STARTING ALL SERVICES IN THE BACKGROUND"
echo "=========================================================================="

# Port cleanup before boot
echo "--- Cleaning up ports (8000, 5173, and 5001) ---"
lsof -t -i :8000 | xargs kill -9 2>/dev/null || true
lsof -t -i :5173 | xargs kill -9 2>/dev/null || true
lsof -t -i :5001 | xargs kill -9 2>/dev/null || true

# --- 1. Start MLflow tracking server ---
echo -e "\n--- ⚙️ Starting MLflow Tracking Server (with Basic-Auth security) ---"
export MLFLOW_AUTH_CONFIG_PATH=$(pwd)/MagellanFrontend/mlflow_users.ini
export MLFLOW_FLASK_SERVER_SECRET_KEY='super-secret-key-for-csrf'
./.venv/bin/mlflow server --host 127.0.0.1 --port 5001 --app-name basic-auth > mlflow_log.txt 2>&1 &
MLFLOW_PID=$!
echo "✅ MLflow Server started on port 5001 with PID: $MLFLOW_PID (Logs: mlflow_log.txt)"

# --- 2. Wait for Temporal and Start Worker ---
echo -e "\n--- ⏳ Waiting for Temporal Server on port 7233 ---"
if [ -f "./MagellanFrontend/.venv/bin/activate" ]; then
    source ./MagellanFrontend/.venv/bin/activate
    python3 temporal/wait_for_server.py
    
    echo "--- ⚙️ Starting Temporal Worker in the background ---"
    python3 temporal/run_worker.py > worker_log.txt 2>&1 &
    WORKER_PID=$!
    echo "✅ Temporal Worker started with PID: $WORKER_PID (Logs: worker_log.txt)"
    deactivate
fi

# --- 3. Start FastAPI Backend App ---
echo -e "\n--- ⚙️ Starting FastAPI Backend App (Uvicorn) ---"
if [ -f "./MagellanFrontend/.venv/bin/activate" ]; then
    source ./MagellanFrontend/.venv/bin/activate
    uvicorn MagellanFrontend.fastapi_app:app --host 0.0.0.0 --port 8000 > backend_log.txt 2>&1 &
    BACKEND_PID=$!
    echo "✅ FastAPI Backend started with PID: $BACKEND_PID (Logs: backend_log.txt)"
    deactivate
fi

# --- 4. Start React Frontend Server ---
echo -e "\n--- ⚙️ Starting Vite React Frontend Console ---"
if [ -d "./MagellanFrontend" ]; then
    cd MagellanFrontend
    # Assuming npm packages are already installed, run dev server
    npm run dev > ../frontend_log.txt 2>&1 &
    FRONTEND_PID=$!
    echo "✅ React Frontend started with PID: $FRONTEND_PID (Logs: frontend_log.txt)"
    cd ..
fi

echo -e "\n=========================================================================="
echo "🎉 SUCCESS: All local services have been initialized and started!"
echo "=========================================================================="
echo "📱 React Frontend Console: http://localhost:5173"
echo "⚙️ FastAPI Backend API:     http://localhost:8000"
echo "📈 MLflow Observability:   http://127.0.0.1:5000"
echo "🌀 Temporal Orchestrator:  http://localhost:8233"
echo "=========================================================================="
echo "🔔 HOW TO MONITOR THE CURRENT TEMPORAL FLOW & ACTIVE PHASES:"
echo "The system runs a sequential, self-healing pipeline (RCA ➔ Fix ➔ Eval ➔ Release)."
echo "You can monitor which phase is currently active in two visual ways:"
echo ""
echo "  A. 💻 The Interactive Timeline (React UI Console Tab):"
echo "     Streams real-time state logs directly from the active Temporal Worker:"
echo "       - [RCA] Chief Investigator running specialized diagnosis agents..."
echo "       - [FIX] GoogleFixProposalAgent generating database schema patch..."
echo "       - [EVAL] MetricsEvaluatorTool running mathematical ranx evaluations..."
echo "       - [APPROVAL] Execution PAUSED (NDCG below safety floor). Waiting..."
echo "       - [RELEASE] Deploying Canary to LanceDB vector database..."
echo "       - [FEEDBACK] Auditing deployment metrics..."
echo ""
echo "  B. 🌀 The Temporal Web UI Dashboard (http://localhost:8233):"
echo "     - Displays the live interactive workflow state-machine graph."
echo "     - Highlights exactly which activity task is running (e.g. root_cause_activity"
echo "       or eval_activity) or if it's waiting for a manual approval signal."
echo "=========================================================================="
echo "🔔 HUMAN APPROVAL GATEWAY:"
echo "If evaluation scores (NDCG) fall below your configured policy floor (e.g. 0.84),"
echo "Temporal enters a paused state. Unpause and approve the rollout in two ways:"
echo "  1. 💻 React Console UI  ➔ Click the red/yellow 'Resolve Now' banner"
echo "  2. ⚡ Command Line Tool  ➔ Run 'python3 temporal/signal_workflow.py <workflow-id>'"
echo "=========================================================================="
echo "Use 'kill -9 <PID>' to stop individual services, or exit this terminal."
echo "=========================================================================="

# Keep the script active and wait for any background process to exit
wait
