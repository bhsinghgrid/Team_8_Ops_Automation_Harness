# Signal API Input And Expected Response Examples

Date: 2026-06-07

This document contains sample request bodies and expected response shapes for the Phase 1 Magellan signal ingestion APIs.

Dynamic fields such as `event_id`, `timestamp`, `latency_ms`, and raw OCS metadata will vary on each run.

## Runtime Notes

- `SEARCH_PROVIDER` defaults to `ocs`.
- If a request omits `tenant`, Magellan uses `OCS_TENANT`, currently `ocs_example`.
- Search requests call OCS; OCS searches the mock catalog after the mock products have been seeded or synced into the OCS Elasticsearch index.
- `mock-data/` contains reproducible seed/demo fixtures. On startup, product and rule fixtures seed the database if the corresponding tables are empty.
- Catalog diff requests mutate the `products` table, sync the mutation to OCS, and flush OCS config.
- Rule diff requests mutate the `rules` table.
- If a request provides the wrong tenant, OCS searches the wrong catalog/index or returns an error.

## 1. Search Result Signal

Endpoint:

```text
POST /signals/search
```

Purpose:

```text
Send one search query to OCS, capture the search result, and store it as a search_result event in ops_events.
```

Sample request:

```json
{
  "query_id": "Q-TRAIL-001",
  "query_text": "waterproof trail shoe",
  "tenant": "ocs_example",
  "limit": 5,
  "offset": 0,
  "filters": {}
}
```

Expected response:

```json
{
  "event_id": "SR-20260607-xxxxxxxxxxxxxxxx",
  "event_type": "search_result",
  "source_capability": "semantic_search",
  "severity": "info",
  "timestamp": "2026-06-07T10:00:00Z",
  "provider": "ocs",
  "tenant": "ocs_example",
  "payload": {
    "provider": "ocs",
    "tenant": "ocs_example",
    "query_id": "Q-TRAIL-001",
    "query_text": "waterproof trail shoe",
    "limit": 5,
    "offset": 0,
    "filters": {},
    "status_code": 200,
    "success": true,
    "latency_ms": 32,
    "result_count": 3,
    "top_product_ids": ["FOOT-001", "FOOT-007", "FOOT-013"],
    "metadata": {},
    "response_payload": {
      "slices": [
        {
          "label": "main",
          "matchCount": 3,
          "hits": [
            {
              "document": {
                "id": "FOOT-001",
                "data": {
                  "title": "Waterproof Trail Runner 001",
                  "category": "footwear",
                  "stock": 23
                }
              }
            }
          ]
        }
      ]
    }
  },
  "created": true
}
```

Why severity is `info`:

```text
OCS returned a successful response with at least one result.
```

## 2. Zero-Result Search Signal

Endpoint:

```text
POST /signals/search
```

Purpose:

```text
Capture a search query where OCS returns zero results and create/update a zero_result_cluster.
```

Sample request:

```json
{
  "query_id": "Q-ZERO-001",
  "query_text": "solar powered smartwatch",
  "tenant": "ocs_example",
  "limit": 5,
  "offset": 0,
  "filters": {}
}
```

Expected response:

```json
{
  "event_id": "SR-20260607-yyyyyyyyyyyyyyyy",
  "event_type": "search_result",
  "source_capability": "semantic_search",
  "severity": "warning",
  "timestamp": "2026-06-07T10:01:00Z",
  "provider": "ocs",
  "tenant": "ocs_example",
  "payload": {
    "provider": "ocs",
    "tenant": "ocs_example",
    "query_id": "Q-ZERO-001",
    "query_text": "solar powered smartwatch",
    "limit": 5,
    "offset": 0,
    "filters": {},
    "status_code": 200,
    "success": true,
    "latency_ms": 54,
    "result_count": 0,
    "top_product_ids": [],
    "metadata": {},
    "response_payload": {
      "slices": [
        {
          "label": "main",
          "matchCount": 0,
          "hits": []
        }
      ]
    }
  },
  "created": true
}
```

Why severity is `warning`:

```text
OCS responded successfully, but result_count = 0.
```

Expected zero-result cluster:

```json
[
  {
    "id": 1,
    "cluster_intent": "solar powered smartwatch",
    "query_examples": ["solar powered smartwatch"],
    "hit_count": 1,
    "first_seen": "2026-06-07T10:01:00Z",
    "last_seen": "2026-06-07T10:01:00Z",
    "status": "open",
    "recommended_runbook": "catalog_qa_agent"
  }
]
```

Check zero-result clusters:

```bash
curl http://127.0.0.1:8000/signals/zero-results
```

## 3. Batch Search Signal

Endpoint:

```text
POST /signals/search/batch
```

Purpose:

```text
Read a query file, send each query to OCS, and store one search_result event per query.
```

Default query file:

```text
mock-data/queries/benchmark_queries.json
```

Sample request:

```json
{
  "queries_file": "mock-data/queries/benchmark_queries.json",
  "tenant": "ocs_example",
  "limit": 10,
  "offset": 0
}
```

Expected response:

```json
{
  "total": 50,
  "succeeded": 50,
  "failed": 0,
  "zero_result_count": 8,
  "event_ids": [
    "SR-20260607-xxxxxxxxxxxxxxxx",
    "SR-20260607-yyyyyyyyyyyyyyyy"
  ],
  "errors": []
}
```

Notes:

```text
total is the number of queries in the selected queries_file.
zero_result_count depends on the current OCS indexed catalog.
event_ids are deterministic per tenant + query + timestamp minute.
```

## 4. Catalog Delta Signal

Endpoint:

```text
POST /signals/catalog-diff
```

Purpose:

```text
Record a product catalog change, mutate database-backed product state, sync the change into OCS, and classify operational severity.
```

Side effects:

```text
1. Stores a catalog_delta event in ops_events.
2. Applies INSERT, UPDATE, or DELETE to the products table.
3. Syncs the same product change to OCS.
4. Flushes OCS config so search can reflect the update.
```

Sample request:

```json
{
  "product_id": "BAGS-999",
  "operation": "INSERT",
  "changed_fields": [],
  "before": null,
  "after": {
    "id": "BAGS-999",
    "title": "Incomplete Bag",
    "description": "Missing searchable attributes",
    "category": "bags",
    "brand": "TestBrand",
    "price": 89,
    "stock": 4,
    "attributes": {
      "laptop_size": "15inch"
    },
    "data_quality": "new_arrival"
  },
  "missing_attributes": ["capacity_liters", "material", "waterproof"]
}
```

Expected response:

```json
{
  "event_id": "CAT-20260607-xxxxxxxx",
  "severity": "critical",
  "event_type": "catalog_delta",
  "message": "Catalog delta ingested and applied for BAGS-999"
}
```

Why severity is `critical`:

```text
operation = INSERT, and required/search-sensitive attributes are missing.
```

Error responses:

```text
409 Conflict      The requested database mutation is invalid, such as UPDATE on a missing product.
502 Bad Gateway  The local event/mutation happened but the OCS sync or flush step failed.
```

## 5. Rule Diff / MXP Signal

Endpoint:

```text
POST /signals/rule-diff
```

Purpose:

```text
Record a merchandising/MXP rule change, mutate database-backed rule state, and classify whether it creates an operational risk.
```

Side effects:

```text
1. Stores a rule_diff event in ops_events.
2. Applies INSERT, UPDATE, or DELETE to the rules table.
```

Sample request:

```json
{
  "rule_id": "MXP-001",
  "rule_type": "boost",
  "operation": "UPDATE",
  "changed_fields": ["boost_factor"],
  "before_state": {
    "boost_factor": 1.33
  },
  "after_state": {
    "boost_factor": 2.1
  },
  "author": "vip",
  "oos_conflicts": [
    {
      "product_id": "FOOT-121",
      "title": "Waterproof Trail Runner Lite 121",
      "stock": 0,
      "conflict": "rule targets out-of-stock product"
    }
  ]
}
```

Expected response:

```json
{
  "event_id": "MXP-20260607-xxxxxxxx",
  "severity": "critical",
  "event_type": "rule_diff",
  "message": "Rule diff ingested and applied for MXP-001"
}
```

Why severity is `critical`:

```text
The boost rule targets an out-of-stock product through oos_conflicts.
```

Activation scenarios:

```text
Rule activation is represented as operation = UPDATE with changed_fields = ["active"] and after_state.active = true.
```

## 6. List Stored Events

Endpoint:

```text
GET /signals/search
```

Purpose:

```text
List stored search_result, catalog_delta, and rule_diff events.
```

Useful filters:

```text
event_type=search_result|catalog_delta|rule_diff
severity=critical|warning|info
zero_results_only=true
from_ts=2026-06-07T00:00:00Z
to_ts=2026-06-08T00:00:00Z
limit=20
offset=0
```

Example:

```bash
curl "http://127.0.0.1:8000/signals/search?event_type=catalog_delta&limit=5"
```

Stored signal responses are saved in:

```text
magellan.public.ops_events.payload
```

Zero-result cluster summaries are saved in:

```text
magellan.public.zero_result_clusters
```

View latest stored events:

```bash
docker exec magellan-postgres psql -U postgres -d magellan \
  -c "SELECT event_id, event_type, severity, payload
      FROM ops_events
      ORDER BY timestamp DESC
      LIMIT 5;"
```

View zero-result clusters:

```bash
docker exec magellan-postgres psql -U postgres -d magellan \
  -c "SELECT id, cluster_intent, hit_count, query_examples, status, recommended_runbook
      FROM zero_result_clusters
      ORDER BY last_seen DESC;"
```

## Swagger Docs

Open:

```text
http://127.0.0.1:8000/docs
```

Swagger shows each endpoint request schema and lets you test the APIs directly.
