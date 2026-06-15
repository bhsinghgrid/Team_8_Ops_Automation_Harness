# AI Agent Instructions for Magellan-signal-ingestion-backend

This document provides essential context for AI coding agents to effectively contribute to the `Magellan-signal-ingestion-backend` codebase.

## 1. Big Picture Architecture
-   **Core Service:** The primary application is a Python-based signal ingestion backend located in `Magellan-signal-ingestion-backend/app`. Its main responsibility is to receive, validate, transform, and persist incoming signals.
-   **Supporting Services:** Local development leverages `docker-compose.yml` to orchestrate external dependencies. Currently, this includes:
    -   `meilisearch:v1.7` for search functionality.
    -   `postgres:16` as the primary relational database.
-   **Data Flow:** Signals typically flow as: External Source -> Ingestion API (in `app/api`) -> Validation/Processing (in `app/services` and `app/core`) -> Persistence (via `app/db` to PostgreSQL) and potentially to MeiliSearch.

## 2. Critical Developer Workflows

### 2.1. Local Environment Setup
To bring up the supporting services:
```bash
docker-compose -f Magellan-signal-ingestion-backend/docker-compose.yml up -d
```
The main Python application is expected to run within its `venv` virtual environment. Activate it using:
```bash
source Magellan-signal-ingestion-backend/venv/bin/activate
# Then install dependencies
pip install -r Magellan-signal-ingestion-backend/requirements.txt
```

### 2.2. Building and Running
-   **Python Application:** Once the `venv` is active and dependencies are installed, the main application can be run by executing its entrypoint (e.g., `python -m uvicorn app.main:app --reload` or a similar command, infer from `app/` structure).
-   **Scripts:** Look in `Magellan-signal-ingestion-backend/scripts` for common development or utility scripts.

### 2.3. Testing
-   **Framework:** The project uses `pytest`. Tests are located in `Magellan-signal-ingestion-backend/tests`.
-   **Execution:** Run all tests from the `Magellan-signal-ingestion-backend` directory with `pytest`.
-   **Integration Tests:** Assume integration tests require the Docker Compose services (`meilisearch`, `postgres`) to be running.

## 3. Project-Specific Conventions and Patterns

-   **Modularity:** The `app` directory is organized into distinct modules (`api`, `db`, `models`, `schemas`, `services`) reflecting responsibilities. When adding new features, follow this modularity.
-   **Data Modeling:** Pydantic models are likely used for data validation and serialization (check `app/schemas` and `app/models`).
-   **Database Interactions:** Database logic is encapsulated within `app/db` and `app/models`.
-   **Configuration:** Environment variables are used for configuring services, especially those defined in `docker-compose.yml` (e.g., `POSTGRES_DB`). Avoid hardcoding values.

## 4. Integration Points and External Dependencies

-   **PostgreSQL:** Database interactions should be handled through the ORM/ODM configured in `app/db`.
-   **MeiliSearch:** Integrations with MeiliSearch will likely involve a client library and indexing logic, probably found in `app/services`.
-   **Signal API:** The `docs/research/signal-api-json-examples` directory is crucial for understanding the expected structure of incoming signals. Any changes to data contracts should reflect here.

## 5. Key Files and Directories

-   `/Users/vipkumar/Magellan/Magellan-signal-ingestion-backend/docker-compose.yml`: Defines local development services.
-   `/Users/vipkumar/Magellan/Magellan-signal-ingestion-backend/requirements.txt`: Python dependencies.
-   `/Users/vipkumar/Magellan/Magellan-signal-ingestion-backend/app/`: Core application logic.
    -   `app/api/`: API endpoints.
    -   `app/db/`: Database connection and utilities.
    -   `app/models/`: Data models.
    -   `app/schemas/`: Data validation schemas (e.g., Pydantic).
    -   `app/services/`: Business logic.
-   `/Users/vipkumar/Magellan/Magellan-signal-ingestion-backend/tests/`: Unit and integration tests.
-   `/Users/vipkumar/Magellan/Magellan-signal-ingestion-backend/scripts/`: Utility and automation scripts.
-   `/Users/vipkumar/Magellan/Magellan-signal-ingestion-backend/docs/research/signal-api-json-examples/`: API examples and research.
