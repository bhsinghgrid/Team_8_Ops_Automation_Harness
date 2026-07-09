# Magellan AI Search Ops Automation Harness

This project is a complete, end-to-end automation platform for monitoring, diagnosing, and repairing AI-powered search systems. It uses a sophisticated pipeline of AI agents orchestrated by Temporal to provide a powerful, self-healing solution for search quality and data integrity issues.

The system is fully containerized with Docker, making it easy to set up and run on any machine.

## 🚀 Features

- **End-to-End Automation**: From signal detection to root cause analysis, fix proposal, evaluation, and release.
- **AI-Powered Agents**: Utilizes the `fast-rlm` library with Google's Gemini models to perform complex analysis and remediation tasks.
- **Temporal Workflows**: Robust, stateful orchestration of the entire agent pipeline.
- **Live Shadow Testing**: Integrated with the Diffy proxy server for safe, real-world evaluation of proposed fixes.
- **Web Interface**: A modern React-based UI for monitoring workflows, triggering new runs, and viewing shadow test reports.
- **Fully Containerized**: The entire application stack (backend, frontend, databases, proxy) is managed with Docker Compose for portability and ease of use.

## ⚙️ Prerequisites

Before you begin, you will need to have the following tools installed on your local machine:

1.  **Docker and Docker Compose**: To build and run the containerized application. Docker Desktop is recommended for Mac and Windows.
2.  **Google Cloud SDK (`gcloud`)**: For authentication with Google Vertex AI.
3.  **Temporal CLI (`tcld`)**: For running the local Temporal development server.

## 🛠️ One-Time Setup & Installation

You only need to perform these steps the first time you set up the project.

### 1. Install Dependencies & Set Up Virtual Environment

Create a clean Python 3.11+ virtual environment and install the required project dependencies:

```bash
# Initialize and activate the virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install package requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root of the project. Here is a complete sample configuration:

```ini
# ==============================================================================
# 🔑 API KEYS (For Google AI Studio Endpoint)
# ==============================================================================
GEMINI_API_KEY="your-google-ai-studio-api-key"
GOOGLE_API_KEY="your-google-ai-studio-api-key"

# ==============================================================================
# ☁️ GOOGLE CLOUD CONFIGURATION (For Vertex AI Endpoint)
# ==============================================================================
# Project & Region IDs
GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
GOOGLE_CLOUD_LOCATION="us-central1"

# Endpoint Router Control:
# - Set to 1 (or True) to route fast-rlm calls to Google Cloud Vertex AI (IAM-auth)
# - Set to 0 (or False) to route fast-rlm calls to Google AI Studio (API-key-auth)
RLM_VERTEX_AI=1

# ==============================================================================
# 📈 EXPERIMENT TRACKING (MLflow Authentication)
# ==============================================================================
MLFLOW_TRACKING_USERNAME="admin"
MLFLOW_TRACKING_PASSWORD="mysecretpassword"

# ==============================================================================
# 🚀 ORCHESTRATION & RUNTIME
# ==============================================================================
TEMPORAL_ADDRESS="localhost:7233"
FAST_RLM_ALLOW_RUN="True"
```

Replace `"your-gcp-project-id"` and `"your-google-ai-studio-api-key"` with your actual Google Cloud Project ID and credentials.

### 3. Authenticate with Google Cloud (When RLM_VERTEX_AI=1)

If routing model calls to Vertex AI, grant the application permissions to use your Google Cloud credentials by logging in via `gcloud`:

```bash
gcloud auth application-default login
```

---

## ▶️ Running the Application

You can easily run the platform services and worker pipelines locally.

### 1. Start the Temporal Server

In a new terminal window, start the local Temporal development server. Leave this running in the background:

```bash
temporal server start-dev
```
---

## ▶️ Running the Application

There are two verified ways to execute and test the Magellan Automation Harness. Choose your preferred running mode:

---

### **Option A: Clean Local Virtual Environment Run (Highly Recommended)**
This approach runs services natively on your local host using active virtual environments, allowing rapid hot-reloads and live tracking logs.

#### **Step 1: Start Temporal Cluster Server**
In a new terminal window, start your local Temporal development server and keep it running:
```bash
temporal server start-dev
```

#### **Step 2: Start the MLflow Server (Port 5001)**
In a new terminal window, activate your `.venv` and start MLflow with Basic Auth on port `5001`:
```bash
# Load root virtual environment
source .venv/bin/activate

# Setup authorization config and start server
export MLFLOW_AUTH_CONFIG_PATH=$(pwd)/MagellanFrontend/mlflow_users.ini
export MLFLOW_FLASK_SERVER_SECRET_KEY='super-secret-key-for-csrf'
mlflow server --host 127.0.0.1 --port 5001 --app-name basic-auth
```

#### **Step 3: Start the Temporal Worker**
In a new terminal window, activate your `.venv`, source your `.env`, and start the Python activity worker:
```bash
# Activate environment and load variables
source .venv/bin/activate
set -a && source .env && set +a

# Add current workspace to Python Path
export PYTHONPATH=$PYTHONPATH:$(pwd)
export PYTHONUNBUFFERED=1

# Start activity worker loop
python3 temporal/run_worker.py
```

#### **Step 4: Start the FastAPI Backend (Port 8000)**
In a new terminal window, start the REST API and ingestion hooks:
```bash
source .venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn MagellanFrontend.backend_app.app:app --host 0.0.0.0 --port 8000 --reload
```

#### **Step 5: Start the React Vite Frontend (Port 5173)**
In a new terminal window, navigate to `MagellanFrontend`, load its node virtual environment, and boot Vite:
```bash
# Navigate to frontend folder
cd MagellanFrontend

# Activate node/npm virtual modules environment
source .venv/bin/activate

# Launch dev dashboard
npm run dev
```

---

### **Option B: Full Containerized Stack (Docker Compose)**
To spin up all services concurrently (FastAPI backend, React frontend, NGINX routes, and database models) inside structured Docker containers, simply run:

```bash
# Build and compose full containerized stack
docker-compose up --build
```
*Note: Ensure your local `.env` variables (e.g. GEMINI_API_KEY) are fully declared beforehand.*

---

## 🚀 Ingestion & Running Workflows

Once all services are running, you can trigger autonomous search remediation workflows either via our modern React UI or using simple terminal trigger commands.

### **Method 1: Trigger via the Live Operator UI (Recommended)**
1. Open the Magellan Ops Dashboard: `http://localhost:5173`
2. Select the **Live Test** tab in the side navigation.
3. Click on any of our **four pre-configured templates** (Catalog, Autocomplete, Semantic, or Merchandising).
4. Select whether to enable **Autonomous Caching** or force a **live sandbox REPL execution run**.
5. Click **Fire Sandbox Signal** and watch real-time console statuses update dynamically!

### **Method 2: Trigger via CLI Workflows Triggers**
Activate your root `.venv` and fire specific domain signals with caching enabled or bypassed:

```bash
# 1. Run Catalog Pipeline (Instant cached run or live sandbox run)
python3 temporal/run_unified_workflow.py catalog
python3 temporal/run_unified_workflow.py catalog --no-cache

# 2. Run Autocomplete Pipeline
python3 temporal/run_unified_workflow.py autocomplete
python3 temporal/run_unified_workflow.py autocomplete --no-cache

# 3. Run Semantic Vector Index Pipeline
python3 temporal/run_unified_workflow.py semantic
python3 temporal/run_unified_workflow.py semantic --no-cache

# 4. Run Merchandising Rules Conflict Pipeline
python3 temporal/run_unified_workflow.py merchandising
python3 temporal/run_unified_workflow.py merchandising --no-cache
```

---

## 🖥️ Operational Port Map & UIs

Your application exposes several rich operational web interfaces when fully loaded:

| Web UI Interface | Service URI Link | Purpose / Description |
| :--- | :--- | :--- |
| **Magellan Ops UI** | `http://localhost:5173` | Interactive operator dashboard, Canary release sliders, audit trials, and Live Test playpen. |
| **MLflow Experiments UI** | `http://localhost:5001` | Tracks evaluation runs, stores JSON artifact payloads, and displays LLM GenAI Trace Spans (Traces tab). |
| **Temporal Cluster UI** | `http://localhost:8233` | Stateful visualization of currently executing or completed agent state machines. |
| **FastAPI REST API Docs** | `http://localhost:8000/docs` | Live OpenAPI interactives for manual signal ingestion queries. |

---
