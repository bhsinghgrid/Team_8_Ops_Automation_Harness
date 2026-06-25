# Phase 1 Signal Ingestion Summary

## Status

Phase 1 is complete.

The Magellan backend can now ingest search, catalog delta, and MXP rule diff signals using the Magellan mock fixture layer. The mock product and rule fixtures are seeded into Postgres on startup; catalog and rule diff requests mutate the database-backed state, and catalog mutations are synced back into OCS so search behavior stays aligned with the updated product data.

## What Was Built

### Mock Data Fixture Layer

- Created the complete seed fixture set under `mock-data/`.
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
- Added database-backed `products` and `rules` state tables. The JSON fixtures remain reproducible seed/demo data, not the runtime source of truth.

### Search Signal Ingestion

- `POST /signals/search` uses OCS as the search provider.
- OCS has been seeded with Magellan mock products.
- Search requests create `search_result` events.
- Swagger placeholder filters such as `additionalProp1` are sanitized before calling OCS.
- Zero-result searches create/update zero-result clusters.

### Catalog Delta Ingestion

- `POST /signals/catalog-diff` now performs full catalog mutation behavior:
  - Creates a `catalog_delta` event.
  - Applies `INSERT`, `UPDATE`, or `DELETE` to the `products` table.
  - Can derive a flat product index from database state when needed.
  - Syncs the same mutation into OCS.
  - Flushes OCS config so search can reflect the update.
- Added `ProductStateManager` for database-backed product mutations and index derivation.
- Updated `scripts/simulate_catalog_deltas.py` so it sends scenario requests to the API and lets the endpoint own database plus OCS mutation.

### MXP Rule Diff Ingestion

- `POST /signals/rule-diff` now performs full rule mutation behavior:
  - Creates a `rule_diff` event.
  - Applies `INSERT`, `UPDATE`, or `DELETE` to the `rules` table.
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
=> mutate products table
=> sync product change to OCS
=> flush OCS config
```

### MXP Rule Diff

```text
POST /signals/rule-diff
=> store rule_diff event
=> mutate rules table
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
```

Test coverage includes:

- Search ingestion and request sanitization.
- Catalog severity classification.
- Catalog product mutation and index derivation.
- Catalog OCS upsert/delete/flush behavior.
- Rule severity classification.
- Rule table mutation for update, insert, and delete.
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
- Catalog delta ingestion with database-backed product mutation and OCS sync.
- MXP rule diff ingestion with rule-state mutation.
- Bulk scenario simulation scripts.
- Automated tests for the implemented ingestion and mutation behavior.

Next phase candidates:

- Agent/runbook automation on top of ingested signals.
- Observation workflows and UI integration.
- Audit/history views for catalog and rule mutations.
- More robust rollback behavior if OCS sync fails after local database mutation.
