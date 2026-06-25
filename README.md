<<<<<<< HEAD
# Team_8_Ops_Automation_Harness
hsdhfdsi
=======
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

## 🛠️ One-Time Setup

You only need to perform these steps the first time you set up the project.

### 1. Configure Environment Variables

Create a `.env` file in the root of the project. This file will store your Google Cloud configuration.

```bash
# .env
GCP_PROJECT_ID="your-gcp-project-id"
GCP_LOCATION="us-central1"
```

Replace `"your-gcp-project-id"` with your actual Google Cloud Project ID.

### 2. Authenticate with Google Cloud

You need to grant the application permission to use your Google Cloud account for the AI models. Run the following command in your terminal and follow the instructions to log in with your Google account:

```bash
gcloud auth application-default login
```

## ▶️ Running the Application

The entire application can be started with just a few commands.

### 1. Start the Temporal Server

In a new terminal window, start the local Temporal development server. Leave this terminal running in the background.

```bash
temporal server start-dev
```

### 2. Start the Application with Docker Compose

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
>>>>>>> d6803d8 (Final Code)
