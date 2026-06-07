# OCSS Stack And Catalog Data Notes

Date: 2026-06-03

This note explains what "OCSS running" means, where OCSS product data lives, and how Magellan relates to OCSS.

## What OCSS Means

OCSS means Open Commerce Search Stack. In this workspace it is located at:

```text
/Users/vipkumar/open-commerce-search
```

It is the search engine that Magellan calls during search ingestion.

## What "OCSS Is Running" Means

It means the Open Commerce Search services are running as Docker containers and responding to HTTP requests.

Main containers:

```text
ocs_searcher        -> OCS Search API backend
ocs_indexer         -> OCS Indexing API backend
ocs_suggest         -> Suggest/autocomplete backend
ocs_elasticsearch   -> Elasticsearch search/index storage
ocs_kibana          -> Kibana UI
```

Important container for Magellan:

```text
ocs_searcher
```

Magellan calls this service through:

```text
http://127.0.0.1:8534
```

Health check:

```bash
curl http://127.0.0.1:8534/search-api/v1/tenants
```

Expected:

```json
["ocs_example"]
```

## Docker Compose Definitions

The OCSS containers are defined in:

```text
open-commerce-search/operations/docker-compose/docker-compose.base.yml
```

Example mapping:

```text
service name: searcher
container name: ocs_searcher
port: 8534
```

Inside Docker Compose, the frontend can call:

```text
http://searcher:8534
```

From your Mac, use:

```text
http://127.0.0.1:8534
```

## Where The OCSS Search Routes Come From

The base path is defined in:

```text
open-commerce-search/search-service/src/main/java/de/cxp/ocs/SearchController.java
```

Controller base:

```java
@RequestMapping(path = "/search-api/v1")
```

Tenants endpoint:

```java
@GetMapping("/tenants")
```

Combined route:

```text
/search-api/v1/tenants
```

Full local URL:

```text
http://127.0.0.1:8534/search-api/v1/tenants
```

Search endpoint used by Magellan:

```text
POST /search-api/v1/search/arranged/{tenant}
```

Full local URL:

```text
http://127.0.0.1:8534/search-api/v1/search/arranged/ocs_example
```

## Where OCSS Product Data Is Stored

OCSS product catalog data is stored in Elasticsearch, not in the Magellan mock files.

Current alias:

```text
ocs_example
```

Current real Elasticsearch index:

```text
ocs-1-ocs_example-en
```

Storage path conceptually:

```text
OCSS -> Elasticsearch -> index ocs-1-ocs_example-en
```

Physical data is inside the Elasticsearch container:

```text
ocs_elasticsearch:/usr/share/elasticsearch/data
```

## Current Demo Catalog

The current indexed OCSS dataset contains products like:

```json
{
  "id": "003",
  "resultData": {
    "title": "Bike Light",
    "brand": "Barfoo",
    "price": 15.99,
    "stock": 3,
    "artNr": "b11",
    "category": ["Sport/Bike Accessories"]
  }
}
```

This product appears in the OCS repository test data:

```text
open-commerce-search/integration-tests/src/test/resources/testdata.jsonl
```

After indexing, it is stored in Elasticsearch.

## Important Distinction: Query Data vs Product Data

Magellan has:

```text
Magellan-backend/mock-data/queries/benchmark_queries.json
Magellan-backend/mock-data/products/products.json
```

Current behavior:

```text
benchmark_queries.json -> can provide search query text for batch ingestion
products.json          -> not currently indexed into OCSS
OCSS Elasticsearch     -> provides actual product search results
```

So if batch ingestion sends:

```text
waterproof running shoes
```

that query may come from Magellan's `benchmark_queries.json`, but OCSS searches its own indexed catalog.

If OCSS returns:

```json
{
  "matchCount": 0,
  "hits": []
}
```

it means the OCSS indexed catalog did not contain matching products, even if Magellan's mock `products.json` contains waterproof shoes.

## View The OCSS Catalog

Show Elasticsearch indices:

```bash
curl 'http://127.0.0.1:9200/_cat/indices?v'
```

Show aliases:

```bash
curl 'http://127.0.0.1:9200/_aliases?pretty'
```

Show first 20 catalog products:

```bash
curl -s 'http://127.0.0.1:9200/ocs_example/_search?pretty&size=20' \
  -H 'Content-Type: application/json' \
  -d '{
    "_source": ["id", "resultData"],
    "query": {
      "match_all": {}
    }
  }'
```

Count products:

```bash
curl -s 'http://127.0.0.1:9200/ocs_example/_count?pretty' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "match_all": {}
    }
  }'
```

## View Catalog In Kibana

Open:

```text
http://localhost:5601
```

Go to:

```text
Dev Tools
```

Run:

```json
GET ocs_example/_search
{
  "_source": ["id", "resultData"],
  "query": {
    "match_all": {}
  },
  "size": 20
}
```

## OCSS Frontend

The frontend is a separate Next.js app:

```text
open-commerce-search/ocss-frontend
```

It can be run with Docker or Node.

### Docker frontend

Use Docker when you want the frontend container on the same Docker network as OCSS:

```bash
cd /Users/vipkumar/open-commerce-search/operations/docker-compose
DEFAULT_TENANT=ocs_example \
NEXTAUTH_SECRET=dev-secret \
NEXTAUTH_URL=http://localhost:3000 \
docker compose -f docker-compose.base.yml -f docker-compose.local.yml -f docker-compose.frontend.yml up -d ocss-frontend
```

Open:

```text
http://localhost:3000
```

### Node frontend

Use Node when developing locally:

```bash
cd /Users/vipkumar/open-commerce-search/ocss-frontend
npm install
SEARCH_API_URL=http://127.0.0.1:8534 \
DEFAULT_TENANT=ocs_example \
NEXTAUTH_SECRET=dev-secret \
NEXTAUTH_URL=http://localhost:3000 \
ENABLE_SUGGEST_API=false \
npm run dev
```

Open:

```text
http://localhost:3000
```

## Environment Variables Explained

```text
DEFAULT_TENANT=ocs_example
```

Tells the frontend which tenant/index to use.

```text
NEXTAUTH_SECRET=dev-secret
```

Required by NextAuth. For local development this can be a dummy string.

```text
NEXTAUTH_URL=http://localhost:3000
```

Tells NextAuth where the frontend is running.

```text
SEARCH_API_URL=http://127.0.0.1:8534
```

Used when frontend runs on your Mac.

```text
SEARCH_API_URL=http://searcher:8534
```

Used when frontend runs inside Docker.

