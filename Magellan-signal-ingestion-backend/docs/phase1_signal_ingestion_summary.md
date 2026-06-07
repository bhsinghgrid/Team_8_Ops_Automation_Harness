# Phase 1 Signal Ingestion Summary

## Status

Phase 1 is complete.

The Magellan backend can now ingest search, catalog delta, and MXP rule diff signals using the Magellan mock fixture layer. Catalog and rule diff requests also mutate the local mock data state, and catalog mutations are synced back into OCS so search behavior stays aligned with the updated product data.

## What Was Built

### Mock Data Fixture Layer

- Created the complete fixture set under `mock-data/`.
- Generated 1000 products across:
  - `products/footwear.json`
  - `products/bags.json`
  - `products/outerwear.json`
  - `products/electronics.json`
  - `products/camping.json`
- Added:
  - `rules/rules.json`
  - `queries/benchmark_queries.json`
  - `queries/zero_result_queries.json`
  - `scenarios/catalog_scenarios.json`
  - `scenarios/rule_scenarios.json`
  - `index/product_index.json`
- Added `scripts/generate_mock_data.py` with generate and validation support.

### Search Signal Ingestion

- `POST /signals/search` uses OCS as the search provider.
- OCS has been seeded with Magellan mock products.
- Search requests create `search_result` events.
- Swagger placeholder filters such as `additionalProp1` are sanitized before calling OCS.
- Zero-result searches create/update zero-result clusters.

### Catalog Delta Ingestion

- `POST /signals/catalog-diff` now performs full catalog mutation behavior:
  - Creates a `catalog_delta` event.
  - Applies `INSERT`, `UPDATE`, or `DELETE` to `mock-data/products/*.json`.
  - Recomputes `mock-data/index/product_index.json`.
  - Syncs the same mutation into OCS.
  - Flushes OCS config so search can reflect the update.
- Added `ProductStateManager` for fixture-safe product mutations and index recomputation.
- Updated `scripts/simulate_catalog_deltas.py` so it sends scenario requests to the API and lets the endpoint own mock-data plus OCS mutation.

### MXP Rule Diff Ingestion

- `POST /signals/rule-diff` now performs full rule mutation behavior:
  - Creates a `rule_diff` event.
  - Applies `INSERT`, `UPDATE`, or `DELETE` to `mock-data/rules/rules.json`.
  - Bumps rule state version and timestamp.
- Added `RuleStateManager.apply_diff`.
- Updated `scripts/simulate_rule_diffs.py` so it sends scenario requests to the API and lets the endpoint own rule mutation.
- Activation scenarios are represented as `UPDATE` operations with `active: false -> true`.

## Current Runtime Model

### Search

```text
POST /signals/search
=> call OCS search
=> store search_result event
```

### Catalog Delta

```text
POST /signals/catalog-diff
=> store catalog_delta event
=> mutate mock-data/products/*.json
=> recompute mock-data/index/product_index.json
=> sync product change to OCS
=> flush OCS config
```

### MXP Rule Diff

```text
POST /signals/rule-diff
=> store rule_diff event
=> mutate mock-data/rules/rules.json
```

## Simulation Scripts

The simulator scripts are now bulk/demo drivers. They send predefined scenario requests to the same API endpoints used by manual testing.

```bash
./venv/bin/python scripts/simulate_catalog_deltas.py
./venv/bin/python scripts/simulate_rule_diffs.py
```

The endpoint owns the mutation behavior. The scripts no longer need to apply duplicate local mutations.

## Verification

The latest verification passed:

```text
34 tests passed
compileall passed
backend health check returned 200 OK
```

Test coverage includes:

- Search ingestion and request sanitization.
- Catalog severity classification.
- Catalog product mutation and index recomputation.
- Catalog OCS upsert/delete/flush behavior.
- Rule severity classification.
- Rule JSON mutation for update, insert, and delete.
- Validation failures for malformed requests.

## Operational Requirements

For full Phase 1 behavior, both systems must be running:

```text
Magellan backend: http://127.0.0.1:8000
OCS stack:        http://127.0.0.1:8534
```

If OCS is stopped, search requests and catalog-to-OCS sync can fail. Catalog delta ingestion returns `502 Bad Gateway` when the OCS sync step fails.

## Completion Verdict

Phase 1 is complete for signal ingestion.

Completed scope:

- Mock data generation and validation.
- Search signal ingestion using OCS seeded with Magellan mock products.
- Catalog delta ingestion with mock-data mutation and OCS sync.
- MXP rule diff ingestion with rule-state mutation.
- Bulk scenario simulation scripts.
- Automated tests for the implemented ingestion and mutation behavior.

Next phase candidates:

- Agent/runbook automation on top of ingested signals.
- Observation workflows and UI integration.
- Audit/history views for catalog and rule mutations.
- More robust rollback behavior if OCS sync fails after local file mutation.
