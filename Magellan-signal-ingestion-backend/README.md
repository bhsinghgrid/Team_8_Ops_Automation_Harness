# Magellan AI Search Ops Harness - Signal Ingestion Backend

This repository contains the backend services for the Magellan AI Search Ops Harness, focusing on the passive log-consumption model. Its primary responsibility is to ingest structured search logs, detect various operational signals (anomalies and changes), and persist these signals for downstream diagnosis and automated runbook generation.

## Table of Contents
1.  [Local Environment Setup](#1-local-environment-setup)
2.  [Generating Mock Data](#2-generating-mock-data)
3.  [Starting the FastAPI Server](#3-starting-the-fastapi-server)
4.  [API Endpoint Testing](#4-api-endpoint-testing)
    *   [Log Ingestion Endpoints (`/logs/*`)](#log-ingestion-endpoints-logs)
    *   [Change Detection Endpoints (`/snapshots/*`)](#change-detection-endpoints-snapshots)
    *   [Dynamic Configuration Endpoints (`/config/*`)](#dynamic-configuration-endpoints-config)
    *   [Raw Log Payloads Endpoint (`/logs/raw`)](#raw-log-payloads-endpoint-logsraw)
5.  [Signal to AI Search Capability Mapping](#5-signal-to-ai-search-capability-mapping)
6.  [How Change Detection Agents Work](#6-how-change-detection-agents-work)

---

## 1. Local Environment Setup

To get the Magellan backend running locally, follow these steps:

### Step 1: Start Background Databases (PostgreSQL only)
Navigate to your project root and start the PostgreSQL container using Docker Compose:
```bash
cd /Users/vipkumar/Magellan/Magellan-signal-ingestion-backend
docker-compose up -d
```
*Expected Output:* You should see output indicating the `magellan-postgres` container is starting or already running.

### Step 2: Install Python Dependencies
Ensure your Python virtual environment is active and all dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Generating Mock Data

The system relies on mock search logs to simulate incoming data and test signal detection.

### Command
```bash
python3 scripts/generate_mock_data.py --output mock-data
```
*Purpose:* This command generates 500 structured search log entries in `mock-data/logs/search_events.jsonl`, including various embedded anomalies (latency spikes, zero-result queries, low CTR, and errors). It also creates mock product and rule data.
*Expected Output:* A JSON summary of generated data, confirming `search_logs: 500`.

---

## 3. Starting the FastAPI Server

Once the databases are up and mock data is generated, you can start the application server.

### Command
```bash
source venv/bin/activate
uvicorn app.main:app --reload
```
*Purpose:* This starts the FastAPI application, enabling API endpoints for log ingestion and change detection. The `--reload` flag automatically restarts the server on code changes.
*Expected Output:* Uvicorn will show output indicating the server is running on `http://127.0.0.1:8000`. Keep this terminal window open.

---

## 4. API Endpoint Testing

Open a **new terminal window** for `curl` commands, or use your web browser to access the **Swagger UI** at `http://127.0.0.1:8000/docs`.

### Log Ingestion Endpoints (`/logs/*`)

These endpoints are responsible for receiving and processing search logs, detecting anomalies, and persisting signals.

#### 4.1. `POST /logs/ingest/file` (Ingest Logs from File)
*   **Description:** Processes a JSONL file containing multiple search log entries. This is your primary end-to-end log ingestion route.
*   **Swagger UI:**
    1.  Go to `http://127.0.0.1:8000/docs`.
    2.  Find and expand the `POST /logs/ingest/file` endpoint.
    3.  Click **"Try it out"**.
    4.  In the `file_path` field within the Request Body, enter:
        ```json
        {
          "file_path": "mock-data/logs/search_events.jsonl"
        }
        ```
    5.  Click the blue **"Execute"** button.
*   **`curl` Command:**
    ```bash
    curl -X 'POST' \
      'http://127.0.0.1:8000/logs/ingest/file' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "file_path": "mock-data/logs/search_events.jsonl"
    }' | jq .
    ```
*   **Expected Response:** A JSON response showing `status: "success"`, `parsed_successfully: 500`, and `detected_signals_count > 0` (expect several signals like `latency_spike`, `zero_results`, `low_ctr`, `error_rate`).

#### 4.2. `GET /logs/signals` (List Detected Signals)
*   **Description:** Retrieves all `OpsEvent`s (detected signals) stored in the PostgreSQL database.
*   **Swagger UI:**
    1.  Go to `http://127.0.0.1:8000/docs`.
    2.  Find and expand the `GET /logs/signals` endpoint.
    3.  Click **"Try it out"**. (You can leave parameters blank or try filtering by `severity` or `signal_type`).
    4.  Click the blue **"Execute"** button.
*   **`curl` Command:**
    ```bash
    curl -X 'GET' \
      'http://127.0.0.1:8000/logs/signals' \
      -H 'accept: application/json' | jq .
    ```
*   **Expected Response:** An array of JSON objects, each representing a `DetectedSignal`. You should see `signal_type` values like `"latency_spike"`, `"zero_results"`, `"low_ctr"`, and `"error_rate"`.

#### 4.3. `GET /logs/stats` (Get Aggregated Statistics)
*   **Description:** Provides aggregated metrics (total logs, error rate, average latency, CTR) based on the raw logs stored in PostgreSQL.
*   **Swagger UI:**
    1.  Go to `http://127.0.0.1:8000/docs`.
    2.  Find and expand the `GET /logs/stats` endpoint.
    3.  Click **"Try it out"**.
    4.  Click the blue **"Execute"** button.
*   **`curl` Command:**
    ```bash
    curl -X 'GET' \
      'http://127.0.0.1:8000/logs/stats' \
      -H 'accept: application/json' | jq .
    ```
*   **Expected Response:** A JSON object similar to:
    ```json
    {
      "total_logs": 500,
      "error_rate": 0.XXX,
      "avg_latency_ms": 0.XXX,
      "ctr": 0.XXX
    }
    ```

#### 4.4. `GET /logs/raw` (List Raw Log Payloads)
*   **Description:** Retrieves and lists the full raw JSON payloads of search log entries stored in the database, with optional time and pagination filters. This is useful for detailed inspection or debugging.
*   **Swagger UI:**
    1.  Go to `http://127.0.0.1:8000/docs`.
    2.  Find and expand the `GET /logs/raw` endpoint.
    3.  Click **"Try it out"**. (You can leave parameters blank or specify `limit`, `offset`, `from_ts`, `to_ts`).
    4.  Click the blue **"Execute"** button.
*   **`curl` Command:**
    ```bash
    curl -X 'GET' \
      'http://127.0.0.1:8000/logs/raw' \
      -H 'accept: application/json' | jq .
    ```
*   **Expected Response:** An array of raw JSON search log entries.

#### 4.5. `POST /logs/ingest` (Ingest Single Log Entry)
*   **Description:** Ingests and processes a single search log entry.
*   **Swagger UI:**
    1.  Go to `http://127.0.0.1:8000/docs`.
    2.  Find and expand the `POST /logs/ingest` endpoint.
    3.  Click **"Try it out"**.
    4.  Modify the example Request Body. To trigger a `latency_spike`, set `latency_ms` to `700`.
        ```json
        {
          "timestamp": "2026-06-06T12:00:00Z",
          "source": "manual_test",
          "tenant": "retail_tenant_001",
          "request_id": "req_single_manual_001",
          "session_id": "sess_test_001",
          "user_id_hash": "usr_test_hash",
          "query": { "text": "test query", "normalized_text": "test query", "filters": {}, "sort": "relevance" },
          "response": { "status_code": 200, "latency_ms": 700, "result_count": 10, "results": [ {"product_id": "PROD-X", "rank": 1, "score": 0.9} ] },
          "interaction": { "clicks": [], "cart_adds": [] },
          "context": { "device_type": "desktop", "channel": "web", "locale": "en-US" },
          "error": null
        }
        ```
    5.  Click **"Execute"**.
*   **`curl` Command:**
    ```bash
    curl -X 'POST' \
      'http://127.0.0.1:8000/logs/ingest' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "timestamp": "2026-06-06T12:00:00Z",
      "source": "manual_test",
      "tenant": "retail_tenant_001",
      "request_id": "req_single_manual_001",
      "session_id": "sess_test_001",
      "user_id_hash": "usr_test_hash",
      "query": { "text": "test query", "normalized_text": "test query", "filters": {}, "sort": "relevance" },
      "response": { "status_code": 200, "latency_ms": 700, "result_count": 10, "results": [ {"product_id": "PROD-X", "rank": 1, "score": 0.9} ] },
      "interaction": { "clicks": [], "cart_adds": [] },
      "context": { "device_type": "desktop", "channel": "web", "locale": "en-US" },
      "error": null
    }' | jq .
    ```
*   **Expected Response:** A JSON response directly showing any `DetectedSignal` objects that were triggered.

#### 4.5. `POST /logs/ingest/batch` (Ingest a Batch of Log Entries)
*   **Description:** Ingests and processes multiple search log entries provided as a JSON array in the request body.
*   **Swagger UI:**
    1.  Go to `http://127.0.0.1:8000/docs`.
    2.  Find and expand the `POST /logs/ingest/batch` endpoint.
    3.  Click **"Try it out"**.
    4.  Modify the example Request Body with your custom batch of logs.
        ```json
        {
          "logs": [
            {
              "timestamp": "2026-06-06T12:01:00Z", "source": "manual_batch", "tenant": "retail_tenant_001",
              "request_id": "req_batch_manual_001", "session_id": "sess_test_002", "user_id_hash": "usr_test_hash_2",
              "query": { "text": "batch item 1", "normalized_text": "batch item 1", "filters": {}, "sort": null },
              "response": { "status_code": 200, "latency_ms": 60, "result_count": 5, "results": [] },
              "interaction": { "clicks": [], "cart_adds": [] },
              "context": { "device_type": "desktop", "channel": "web", "locale": "en-US" },
              "error": null
            },
            {
              "timestamp": "2026-06-06T12:02:00Z", "source": "manual_batch", "tenant": "retail_tenant_001",
              "request_id": "req_batch_manual_002", "session_id": "sess_test_003", "user_id_hash": "usr_test_hash_3",
              "query": { "text": "batch item 2", "normalized_text": "batch item 2", "filters": {}, "sort": null },
              "response": { "status_code": 200, "latency_ms": 70, "result_count": 0, "results": [] },
              "interaction": { "clicks": [], "cart_adds": [] },
              "context": { "device_type": "mobile", "channel": "web", "locale": "en-US" },
              "error": null
            }
          ]
        }
        ```
    5.  Click **"Execute"**.
*   **`curl` Command:**
    ```bash
    curl -X 'POST' \
      'http://127.0.0.1:8000/logs/ingest/batch' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "logs": [
        {
          "timestamp": "2026-06-06T12:01:00Z", "source": "manual_batch", "tenant": "retail_tenant_001",
          "request_id": "req_batch_manual_001", "session_id": "sess_test_002", "user_id_hash": "usr_test_hash_2",
          "query": { "text": "batch item 1", "normalized_text": "batch item 1", "filters": {}, "sort": null },
          "response": { "status_code": 200, "latency_ms": 60, "result_count": 5, "results": [] },
          "interaction": { "clicks": [], "cart_adds": [] },
          "context": { "device_type": "desktop", "channel": "web", "locale": "en-US" },
          "error": null
        },
        {
          "timestamp": "2026-06-06T12:02:00Z", "source": "manual_batch", "tenant": "retail_tenant_001",
          "request_id": "req_batch_manual_002", "session_id": "sess_test_003", "user_id_hash": "usr_test_hash_3",
          "query": { "text": "batch item 2", "normalized_text": "batch item 2", "filters": {}, "sort": null },
          "response": { "status_code": 200, "latency_ms": 70, "result_count": 0, "results": [] },
          "interaction": { "clicks": [], "cart_adds": [] },
          "context": { "device_type": "mobile", "channel": "web", "locale": "en-US" },
          "error": null
        }
      ]
    }' | jq .
    ```
*   **Expected Response:** A summary of ingested logs and detected signals for the batch.

### Change Detection Endpoints (`/snapshots/*`)

These endpoints allow you to push "snapshots" of your catalog or MXP rules to Magellan, which then detects if anything has changed from the *last received* snapshot. Signals (`CATALOG_DELTA`, `MXP_RULE_DIFF`) are emitted only when a difference is detected.

#### 4.6. `POST /snapshots/catalog` (Detect Catalog Changes)
*   **Description:** Receives a snapshot of your catalog data and compares it against the previously stored state.
*   **Important Note:** The `STATE_STORE` for previous snapshots is currently in-memory. If your FastAPI server restarts, the previous state will be `None`, and the first `POST` will always trigger a `CATALOG_DELTA`.

**First Call (Initial Snapshot):**
*   **Swagger UI:**
    1.  Go to `http://127.0.0.1:8000/docs`.
    2.  Find and expand the `POST /snapshots/catalog` endpoint.
    3.  Click **"Try it out"**.
    4.  In the Request Body, enter your initial catalog payload:
        ```json
        {
          "products": [
            {"id": "CAT-001", "name": "Adventure Backpack", "price": 85},
            {"id": "CAT-002", "name": "Hiking Pole", "price": 30, "stock": 100}
          ]
        }
        ```
    5.  Click **"Execute"**.
    *Expected Response in UI:* `changed: true`, `signals_emitted: 1`.
*   **`curl` Command:**
    ```bash
    curl -X 'POST' \
      'http://127.0.0.1:8000/snapshots/catalog' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "products": [
        {"id": "CAT-001", "name": "Adventure Backpack", "price": 85},
        {"id": "CAT-002", "name": "Hiking Pole", "price": 30, "stock": 100}
      ]
    }' | jq .
    ```
    *Expected Response:* `{"status": "success", "changed": true, "signals_emitted": 1}`

**Second Call (No Change):**
*   **Swagger UI:** Repeat the steps above, using the **identical** payload.
*   **`curl` Command:** Repeat the `curl` command exactly as above.
*   **Expected Response:** `{"status": "success", "changed": false, "signals_emitted": 0}` (No signal will be emitted).

**Third Call (Catalog Change):**
*   **Swagger UI:** Repeat the steps, but **modify the payload** (e.g., change a price, add a product).
    ```json
    {
      "products": [
        {"id": "CAT-001", "name": "Adventure Backpack", "price": 85},
        {"id": "CAT-002", "name": "Hiking Pole", "price": 28, "stock": 95},  
        {"id": "CAT-003", "name": "Water Bottle", "price": 15}             
      ]
    }
    ```
*   **`curl` Command:**
    ```bash
    curl -X 'POST' \
      'http://127.0.0.1:8000/snapshots/catalog' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "products": [
        {"id": "CAT-001", "name": "Adventure Backpack", "price": 85},
        {"id": "CAT-002", "name": "Hiking Pole", "price": 28, "stock": 95},
        {"id": "CAT-003", "name": "Water Bottle", "price": 15}
      ]
    }' | jq .
    ```
*   **Expected Response:** `{"status": "success", "changed": true, "signals_emitted": 1}`.
*You can verify these `CATALOG_DELTA` signals appear in the `/logs/signals` output.*

#### 4.7. `POST /snapshots/rules` (Detect MXP Rule Changes)
*   **Description:** Receives a snapshot of your MXP rules and compares it against the previously stored state.

**First Call (Initial Snapshot):**
*   **Swagger UI:**
    1.  Go to `http://127.0.0.1:8000/docs`.
    2.  Find and expand the `POST /snapshots/rules` endpoint.
    3.  Click **"Try it out"**.
    4.  In the Request Body, enter your initial MXP rules payload:
        ```json
        {
          "rules": [
            {"id": "RULE-001", "type": "boost", "query": "running shoes", "factor": 1.5},
            {"id": "RULE-002", "type": "synonym", "terms": ["sneakers", "trainers"]}
          ]
        }
        ```
    5.  Click **"Execute"**.
    *Expected Response in UI:* `changed: true`, `signals_emitted: 1`.
*   **`curl` Command:**
    ```bash
    curl -X 'POST' \
      'http://127.0.0.1:8000/snapshots/rules' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "rules": [
        {"id": "RULE-001", "type": "boost", "query": "running shoes", "factor": 1.5},
        {"id": "RULE-002", "type": "synonym", "terms": ["sneakers", "trainers"]}
      ]
    }' | jq .
    ```
    *Expected Response:* `{"status": "success", "changed": true, "signals_emitted": 1}`

**Second Call (No Change):**
*   **Swagger UI:** Repeat the steps above, using the **identical** payload.
*   **`curl` Command:** Repeat the `curl` command exactly as above.
*   **Expected Response:** `{"status": "success", "changed": false, "signals_emitted": 0}`.

**Third Call (Rule Change):**
*   **Swagger UI:** Repeat the steps, but **modify the payload**.
    ```json
    {
      "rules": [
        {"id": "RULE-001", "type": "boost", "query": "running shoes", "factor": 1.8},
        {"id": "RULE-002", "type": "synonym", "terms": ["sneakers", "trainers", "joggers"]}
      ]
    }
    ```
*   **`curl` Command:**
    ```bash
    curl -X 'POST' \
      'http://127.0.0.1:8000/snapshots/rules' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "rules": [
        {"id": "RULE-001", "type": "boost", "query": "running shoes", "factor": 1.8},
        {"id": "RULE-002", "type": "synonym", "terms": ["sneakers", "trainers", "joggers"]}
      ]
    }' | jq .
    ```
*   **Expected Response:** `{"status": "success", "changed": true, "signals_emitted": 1}`.
*You can verify these `MXP_RULE_DIFF` signals appear in the `/logs/signals` output.*

---

## 5. Signal to AI Search Capability Mapping

For a detailed understanding of how each of the detected signals (`latency_spike`, `zero_results`, `low_ctr`, `error_rate`, `CATALOG_DELTA`, `MXP_RULE_DIFF`) maps to specific Grid Dynamics AI Search capabilities (like Semantic Vector Search, Catalog Optimization, etc.) during the "Diagnosis" phase, please refer to:

[`docs/signal_to_capability_mapping.md`](./docs/signal_to_capability_mapping.md)

---

## 6. How Change Detection Agents Work

The `CATALOG_DELTA` and `MXP_RULE_DIFF` signals are generated by the `ChangeDetectionAgent` (`app/agents/change_detection_agent.py`). This agent operates on a snapshot-based comparison using hash digests:

*   **Not a Database Snapshotter:** The agent **does not** directly connect to or query your external catalog or MXP databases.
*   **API-Driven:** It functions by receiving a "current snapshot" (a full JSON payload of the data) via its dedicated API endpoints (`/snapshots/catalog`, `/snapshots/rules`).
*   **Hash Comparison:** It compares the SHA-256 hash of the incoming `current_snapshot` with the hash of the `previous_snapshot` it has stored internally (currently in an in-memory `STATE_STORE`).
*   **Signal Emission:** If the hashes differ, a high-level `DetectedSignal` (either `CATALOG_DELTA` or `MXP_RULE_DIFF`) is emitted and persisted to Magellan's PostgreSQL `ops_events` table.
*   **State Update:** The incoming `current_snapshot` then replaces the `previous_snapshot` in the `STATE_STORE` for future comparisons.

*In a production environment, the in-memory `STATE_STORE` would be replaced by a persistent storage solution (e.g., PostgreSQL, Redis, S3) to ensure state is maintained across server restarts.*
