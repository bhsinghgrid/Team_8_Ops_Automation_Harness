# Magellan AI Search Ops UI

React + Vite frontend with a FastAPI backend bridge for runbooks, audit records, query clusters, and Temporal workflow links.

## Prerequisites

- Node.js 18 or newer
- Python 3.10 or newer
- Temporal Web running locally only if you want the Temporal link to open:

```bash
http://localhost:8233/namespaces/default/workflows
```

## First-Time Setup

Clone or copy the project, then install frontend dependencies:

```bash
npm install
```

Create the local environment file:

```bash
cp .env.example .env
```

Install backend dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Environment Values

The app reads URLs and backend settings from `.env`.

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
TEMPORAL_WORKFLOWS_URL=http://localhost:8233/namespaces/default/workflows
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FRONTEND_ORIGIN_REGEX=http://(localhost|127\.0\.0\.1|0\.0\.0\.0):[0-9]+
```

If you change `.env`, restart both the backend and frontend.

## Start Backend

Run this in terminal 1:

```bash
source .venv/bin/activate
python3 run_fastapi.py
```

Backend will run at:

```bash
http://127.0.0.1:8000
```

Useful backend checks:

```bash
http://127.0.0.1:8000/
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/runbooks
```

## Start Frontend

Run this in terminal 2:

```bash
npm run dev
```

Open the Vite URL shown in the terminal. Usually it is:

```bash
http://localhost:5173
```

## Build Check

Before sharing or deploying, run:

```bash
npm run build
python3 -m py_compile fastapi_app.py run_fastapi.py
```

## Troubleshooting

If the UI shows `Backend not reachable`, start the backend first:

```bash
python3 run_fastapi.py
```

If the frontend is using the wrong backend URL, check `VITE_API_BASE_URL` in `.env`.

If the browser blocks API calls, check `FRONTEND_ORIGINS` and `FRONTEND_ORIGIN_REGEX` in `.env`.

If the Temporal button does not open workflows, check that Temporal Web is running and update `TEMPORAL_WORKFLOWS_URL` in `.env`.

## Current Data Source

The FastAPI backend currently serves local runbook, audit, query-cluster, monitoring, approval, agent, and Temporal metadata from `fastapi_app.py`. Replace those data sections or connect real pipeline APIs later without changing the frontend API structure.
