## Magellan Signal Ingestion Backend

This service is the Phase 1 signal-ingestion layer. It stores normalized search, catalog, and rule signals in `ops_events` and can optionally forward each created event to a Phase 2 pipeline.

## Configure URLs

Copy `.env.example` to `.env` and change endpoints there instead of editing Python files.

```env
MAGELLAN_API_URL=http://127.0.0.1:8000
OCS_SEARCH_URL=http://127.0.0.1:8534
OCS_SEARCH_PATH_TEMPLATE=/search-api/v1/search/arranged/{tenant}
MEILISEARCH_URL=http://localhost:7700
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/magellan
```

## Phase 2 Pipeline Handoff

Enable downstream forwarding when the next pipeline is ready:

```env
DOWNSTREAM_PIPELINE_ENABLED=true
DOWNSTREAM_PIPELINE_URL=http://127.0.0.1:9000
DOWNSTREAM_PIPELINE_EVENTS_PATH=/events
DOWNSTREAM_PIPELINE_AUTH_TOKEN=
```

When enabled, the backend posts a normalized event envelope to:

```text
POST {DOWNSTREAM_PIPELINE_URL}{DOWNSTREAM_PIPELINE_EVENTS_PATH}
```

The payload includes `idempotency_key`, `event_id`, `event_type`, `severity`, `tenant`, `provider`, timestamps, and the original normalized `payload`. Phase 2 should use `idempotency_key` or `event_id` to avoid duplicate processing.

Forwarding is best-effort and non-blocking. If Phase 2 is down, Phase 1 ingestion still succeeds and the failure is logged.
