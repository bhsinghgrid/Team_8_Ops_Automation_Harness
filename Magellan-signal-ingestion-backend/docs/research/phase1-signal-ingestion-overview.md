# Phase 1 Signal Ingestion Overview

Date: 2026-06-03

This note summarizes the Magellan Phase 1 implementation: how search signals are captured, what is stored, and how catalog/rule signals work.

## What Was Implemented

Magellan now has a Phase 1 signal ingestion layer that can:

- Send search queries to Open Commerce Search Stack (OCSS).
- Store normalized search-result signals in Postgres.
- Create or update zero-result query clusters.
- Accept manually reported catalog delta and rule diff signals.
- Classify signal severity as `critical`, `warning`, or `info`.
- Expose stored signals through API endpoints.

Main files:

- `app/api/signals.py`: API routes.
- `app/schemas/signal_schema.py`: request and response schemas.
- `app/services/ingestion_service.py`: signal ingestion and persistence logic.
- `app/providers/ocs_search_provider.py`: OCSS search API integration.
- `app/models/observation.py`: SQLAlchemy models for stored tables.
- `app/core/config.py`: runtime configuration.

## Core Workflow

Search ingestion flow:

```text
Magellan endpoint
-> OCS provider calls Open Commerce Search
-> OCS returns search response
-> Magellan extracts result_count, latency, top products, metadata
-> Magellan stores one row in ops_events
-> If result_count = 0, Magellan updates zero_result_clusters
```

The OCSS provider calls:

```text
POST http://127.0.0.1:8534/search-api/v1/search/arranged/ocs_example
```

Configured in `.env`:

```env
SEARCH_PROVIDER=ocs
OCS_SEARCH_URL=http://127.0.0.1:8534
OCS_TENANT=ocs_example
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/magellan
```

## Stored Tables

### `ops_events`

This is the main canonical signal ledger.

Columns:

```text
event_id
event_type
source_capability
severity
timestamp
provider
tenant
payload
```

Supported `event_type` values:

```text
search_result
catalog_delta
rule_diff
```

Example `search_result` payload:

```json
{
  "query_id": "Q001",
  "query_text": "waterproof running shoes",
  "provider": "ocs",
  "tenant": "ocs_example",
  "status_code": 200,
  "success": true,
  "latency_ms": 50,
  "result_count": 0,
  "top_product_ids": [],
  "metadata": {
    "query_strategy": "relaxed-query"
  },
  "response_payload": {
    "slices": [
      {
        "matchCount": 0,
        "hits": []
      }
    ]
  }
}
```

### `zero_result_clusters`

This table is derived from successful search-result signals with `result_count = 0`.

Columns:

```text
id
cluster_intent
query_examples
hit_count
first_seen
last_seen
status
recommended_runbook
```

Example:

```json
{
  "cluster_intent": "waterproof running shoes",
  "query_examples": ["waterproof running shoes"],
  "hit_count": 2,
  "status": "open",
  "recommended_runbook": "catalog_qa_agent"
}
```

## Query Source

Search queries come from two places.

### Single query API

When calling:

```text
POST /signals/search
```

the query comes from the request body:

```json
{
  "query_id": "Q001",
  "query_text": "waterproof running shoes",
  "tenant": "ocs_example",
  "limit": 5,
  "offset": 0,
  "filters": {}
}
```

### Batch API

When calling:

```text
POST /signals/search/batch
```

Magellan reads:

```text
mock-data/queries/benchmark_queries.json
```

Each item contains a `query_text`:

```json
{
  "query_id": "Q001",
  "query_text": "waterproof running shoes",
  "expected_category": "Footwear"
}
```

Magellan sends every `query_text` to OCSS and stores one `search_result` event per query.

## Zero-Result Clustering

Zero-result clustering is automatic for successful OCSS responses where:

```text
result_count = 0
```

Normalization rule:

```text
lowercase + remove stopwords: a, the, for, with
```

Example:

```text
"The waterproof shoes for trail"
-> "waterproof shoes trail"
```

If the normalized query already exists as `cluster_intent`, Magellan increments `hit_count`.

If no cluster exists, Magellan creates a new one.

## Catalog Delta Signals

Endpoint:

```text
POST /signals/catalog-diff
```

This does not update the real product catalog. It only records that a catalog change was reported to Magellan.

Request body:

```json
{
  "product_id": "P999",
  "operation": "INSERT",
  "changed_fields": [],
  "before": {},
  "after": {
    "title": "Trail Shoe",
    "description": "Waterproof trail shoe",
    "category": "Footwear",
    "brand": "TrailMax",
    "attributes": ["waterproof", "trail"]
  }
}
```

Meaning of `operation`:

```text
INSERT -> product was added
UPDATE -> product was changed
DELETE -> product was removed
```

Severity logic:

```text
critical -> INSERT missing title, description, category, brand, or attributes
warning  -> UPDATE changed title, description, category, brand, or attributes
info     -> otherwise
```

Important: `catalog_delta` currently means "reported catalog change", not "Magellan changed the catalog".

## Rule Diff Signals

Endpoint:

```text
POST /signals/rule-diff
```

Request body:

```json
{
  "rule_id": "R1",
  "rule_type": "boost",
  "before_state": {},
  "after_state": {
    "targets": [
      {
        "product_id": "P999",
        "stock": 0
      }
    ]
  },
  "author": "vip"
}
```

Severity logic:

```text
critical -> after_state targets an out-of-stock product
warning  -> otherwise
```

Out-of-stock detection checks:

```text
stock == 0
inventory_status == "out_of_stock"
targeted product objects with those values
```

## Useful API Commands

Search ingestion:

```bash
curl -X POST http://127.0.0.1:8000/signals/search \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "Q001",
    "query_text": "waterproof running shoes",
    "tenant": "ocs_example",
    "limit": 5,
    "offset": 0,
    "filters": {}
  }'
```

Batch ingestion:

```bash
curl -X POST http://127.0.0.1:8000/signals/search/batch \
  -H "Content-Type: application/json" \
  -d '{}'
```

List stored events:

```bash
curl 'http://127.0.0.1:8000/signals/search?limit=5'
```

List zero-result clusters:

```bash
curl http://127.0.0.1:8000/signals/zero-results
```

Catalog delta:

```bash
curl -X POST http://127.0.0.1:8000/signals/catalog-diff \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "P999",
    "operation": "INSERT",
    "changed_fields": [],
    "before": {},
    "after": {
      "title": "Trail Shoe",
      "description": "Waterproof trail shoe",
      "category": "Footwear",
      "brand": "TrailMax"
    }
  }'
```

The above should become `critical` because `attributes` is missing.

Rule diff:

```bash
curl -X POST http://127.0.0.1:8000/signals/rule-diff \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": "R1",
    "rule_type": "boost",
    "before_state": {},
    "after_state": {
      "targets": [
        {
          "product_id": "P999",
          "stock": 0
        }
      ]
    },
    "author": "vip"
  }'
```

The above should become `critical`.

## Tests

Run from `Magellan-backend`:

```bash
./venv/bin/python -m pytest -q
```

Expected:

```text
6 passed
```

