# Postgres And Signal Visibility Notes

Date: 2026-06-03

This note explains where Magellan stores signals, how to inspect them, and how to troubleshoot "empty table" confusion.

## Database Connection

Magellan uses Docker Postgres:

```text
container: magellan-postgres
host: 127.0.0.1
port: 5433
user: postgres
password: postgres
database: magellan
```

Configured in `.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/magellan
```

## Maintenance DB vs App DB

In GUI tools like pgAdmin, DBeaver, or Postico, it is okay to use:

```text
maintenance database: postgres
```

But the Magellan tables live in:

```text
database: magellan
schema: public
```

If you only view the `postgres` database, you may see no Magellan data.

Correct place:

```text
Databases
-> magellan
-> Schemas
-> public
-> Tables
-> ops_events
-> zero_result_clusters
```

## Main Tables

Phase 1 stores data primarily in:

```text
magellan.public.ops_events
magellan.public.zero_result_clusters
```

The old table:

```text
magellan.public.observations
```

exists but is not the main Phase 1 table. It can be empty.

## Current Expected Data

After our smoke tests, the database contained:

```text
ops_events: 4
zero_result_clusters: 1
observations: 0
```

It is normal for `observations` to be empty.

## Check Data From Terminal

List databases:

```bash
docker exec magellan-postgres psql -U postgres -d postgres \
  -c "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;"
```

Expected:

```text
magellan
postgres
```

Count rows:

```bash
docker exec magellan-postgres psql -U postgres -d magellan \
  -c "SELECT 'ops_events' AS table_name, count(*) FROM ops_events
      UNION ALL
      SELECT 'zero_result_clusters', count(*) FROM zero_result_clusters
      UNION ALL
      SELECT 'observations', count(*) FROM observations;"
```

View latest ops events:

```bash
docker exec magellan-postgres psql -U postgres -d magellan \
  -c "SELECT event_id, event_type, source_capability, severity, provider, tenant, timestamp
      FROM ops_events
      ORDER BY timestamp DESC
      LIMIT 10;"
```

View zero-result clusters:

```bash
docker exec magellan-postgres psql -U postgres -d magellan \
  -c "SELECT id, cluster_intent, hit_count, query_examples, status, recommended_runbook
      FROM zero_result_clusters
      ORDER BY last_seen DESC;"
```

View payload fields:

```bash
docker exec magellan-postgres psql -U postgres -d magellan \
  -c "SELECT event_id,
             event_type,
             severity,
             payload->>'query_text' AS query_text,
             payload->>'product_id' AS product_id,
             payload->>'rule_id' AS rule_id
      FROM ops_events
      ORDER BY timestamp DESC
      LIMIT 10;"
```

## Check Data From API

Swagger:

```text
http://127.0.0.1:8000/docs
```

List stored signals:

```bash
curl 'http://127.0.0.1:8000/signals/search?limit=5'
```

List only search-result events:

```bash
curl 'http://127.0.0.1:8000/signals/search?event_type=search_result&limit=5'
```

List critical events:

```bash
curl 'http://127.0.0.1:8000/signals/search?severity=critical&limit=5'
```

List zero-result-only search events:

```bash
curl 'http://127.0.0.1:8000/signals/search?zero_results_only=true&limit=5'
```

List zero-result clusters:

```bash
curl 'http://127.0.0.1:8000/signals/zero-results'
```

## Start Required Services

Start Magellan Postgres:

```bash
cd /Users/vipkumar/Magellan-backend
docker compose up -d postgres
```

Start Magellan backend:

```bash
cd /Users/vipkumar/Magellan-backend
./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check Magellan backend:

```bash
curl http://127.0.0.1:8000/
```

Expected:

```json
{"message":"Magellan backend is running"}
```

Check OCSS searcher:

```bash
curl http://127.0.0.1:8534/search-api/v1/tenants
```

Expected:

```json
["ocs_example"]
```

## Which Endpoints Need OCSS Running

These call OCSS and need `ocs_searcher` running:

```text
POST /signals/search
POST /signals/search/batch
POST /observations/ingest
```

These do not call OCSS:

```text
GET /signals/search
GET /signals/zero-results
POST /signals/catalog-diff
POST /signals/rule-diff
GET /
```

Most endpoints still need Postgres because they read or write stored signal data.

## Troubleshooting Empty Tables

If your GUI shows no rows:

1. Confirm you are using port `5433`, not `5432`.
2. Confirm you are looking at database `magellan`, not only the maintenance database `postgres`.
3. Confirm schema is `public`.
4. Remember that `observations` can be empty; check `ops_events`.
5. Run this SQL:

```sql
SELECT current_database(), current_schema(), inet_server_port();
```

Expected database:

```text
magellan
```

In pgAdmin, right-click:

```text
ops_events -> View/Edit Data -> All Rows
```

## Useful SQL Examples

All stored events:

```sql
SELECT event_id, event_type, severity, provider, tenant, timestamp
FROM ops_events
ORDER BY timestamp DESC;
```

Full JSON payload:

```sql
SELECT event_id, payload
FROM ops_events
ORDER BY timestamp DESC
LIMIT 3;
```

Search-result payload summary:

```sql
SELECT event_id,
       payload->>'query_text' AS query_text,
       payload->>'result_count' AS result_count,
       payload->>'latency_ms' AS latency_ms
FROM ops_events
WHERE event_type = 'search_result'
ORDER BY timestamp DESC;
```

Catalog deltas:

```sql
SELECT event_id,
       severity,
       payload->>'product_id' AS product_id,
       payload->>'operation' AS operation,
       payload->'missing_embedding_fields' AS missing_embedding_fields
FROM ops_events
WHERE event_type = 'catalog_delta'
ORDER BY timestamp DESC;
```

Rule diffs:

```sql
SELECT event_id,
       severity,
       payload->>'rule_id' AS rule_id,
       payload->>'rule_type' AS rule_type,
       payload->>'targets_out_of_stock_product' AS targets_out_of_stock_product
FROM ops_events
WHERE event_type = 'rule_diff'
ORDER BY timestamp DESC;
```

