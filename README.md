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

### 2. Start the MLflow Server

In a new terminal window, start the MLflow server with basic authentication enabled:

```bash
# Activate your environment
source .venv/bin/activate

# Configure basic auth and launch MLflow
export MLFLOW_AUTH_CONFIG_PATH=$(pwd)/MagellanFrontend/mlflow_users.ini
export MLFLOW_FLASK_SERVER_SECRET_KEY='super-secret-key-for-csrf'
mlflow server --host 127.0.0.1 --port 5000 --app-name basic-auth
```

### 3. Start the Temporal Worker

In a new terminal window, start the Python worker that polls the task queue and executes the repair activities:

```bash
# Activate your environment
source .venv/bin/activate

# Configure and run the worker
export FAST_RLM_ALLOW_RUN="True"
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export PYTHONUNBUFFERED=1
python temporal/run_worker.py
```

### 4. Start the Magellan Frontend & Backend App

In a new terminal window, run the FastAPI backend server:

```bash
# Activate your environment
source .venv/bin/activate

# Start backend server on port 8000
uvicorn MagellanFrontend.backend_app.app:app --host 0.0.0.0 --port 8000
```

To run the full stack containerized with Docker, simply execute:

```bash
docker-compose up --build
```

### 5. Trigger a Repair Workflow

To trigger a new repair run (e.g. `catalog`, `autocomplete`, or `semantic`) from the CLI:

```bash
# Activate your environment
source .venv/bin/activate

# Trigger the workflow (available: catalog, autocomplete, semantic)
python3 temporal/run_unified_workflow.py catalog
```

This will run the entire orchestration pipeline (RCA -> Fix Proposal -> Diffy Evaluation -> Release). You can monitor progress and view deep traces in the web UI.

---

In the root directory of the project, run the following command. This will build the Docker images for the backend and frontend and start all the necessary services.

```bash
docker-compose up --build
```

The first time you run this, it may take a few minutes to download and build everything. Subsequent runs will be much faster.

### 3. Trigger a Workflow

Once all the services are running, you can trigger a new workflow. The system is pre-configured to use the `Catalog/search_events.jsonl` file as the input for the `catalog` workflow.

In a new terminal window, run the following command:

```bash
# Make sure your Python virtual environment is active
source .venv/bin/activate

# Trigger the workflow
python3 temporal/run_unified_workflow.py catalog
```

This will start a new workflow run, which you can monitor in the web UI.

## 🖥️ Accessing the UIs

Your application exposes several web interfaces:

- **Magellan Ops UI**: `http://localhost:5173`
  - This is the main dashboard for monitoring your workflows and viewing results.
- **Diffy UI**: `http://localhost:8888`
  - The web interface for the Diffy shadow testing server.
- **Temporal UI**: `http://localhost:8233`
  - The standard Temporal web UI for inspecting workflows and activities.
