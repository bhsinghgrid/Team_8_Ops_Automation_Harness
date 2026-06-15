# Provider Errors in Mock Search Logs

This document provides examples of search log entries from `mock-data/logs/search_events.jsonl` that represent provider-side (internal server) errors. These typically manifest as HTTP `500 Internal Server Error` or `503 Service Unavailable` status codes and an `error` field set to `"provider_error"`.

Provider errors indicate issues within the search service or its internal dependencies, preventing it from fulfilling a valid request.

---

## Example 1: Service Unavailable (503)

This log simulates the search service being temporarily unavailable, leading to a 503 status code.

```json
{
  "timestamp": "2026-06-06T11:15:40Z",
  "source": "gd_ai_search",
  "tenant": "retail_tenant_001",
  "request_id": "req_20260606_0454",
  "session_id": "sess_005",
  "user_id_hash": "usr_005",
  "query": {
    "text": "smartwatch with gps",
    "normalized_text": "smartwatch gps",
    "filters": {},
    "sort": null
  },
  "response": {
    "status_code": 503,
    "latency_ms": 11342,
    "result_count": 0,
    "results": []
  },
  "interaction": {
    "clicks": [],
    "cart_adds": []
  },
  "context": {
    "device_type": "mobile",
    "channel": "web",
    "locale": "en-US"
  },
  "error": "provider_error"
}
```

---

## Example 2: Internal Server Error (500)

This log simulates an unexpected internal error within the search service's logic, resulting in a 500 status code.

```json
{
  "timestamp": "2026-06-06T11:15:50Z",
  "source": "gd_ai_search",
  "tenant": "retail_tenant_001",
  "request_id": "req_20260606_0455",
  "session_id": "sess_006",
  "user_id_hash": "usr_006",
  "query": {
    "text": "canvas messenger bag",
    "normalized_text": "canvas messenger bag",
    "filters": {},
    "sort": null
  },
  "response": {
    "status_code": 500,
    "latency_ms": 11365,
    "result_count": 0,
    "results": []
  },
  "interaction": {
    "clicks": [],
    "cart_adds": []
  },
  "context": {
    "device_type": "tablet",
    "channel": "web",
    "locale": "en-US"
  },
  "error": "provider_error"
}
```

---

## Example 3: Another Service Unavailable (503)

Another instance of the search service being unavailable.

```json
{
  "timestamp": "2026-06-06T11:17:20Z",
  "source": "gd_ai_search",
  "tenant": "retail_tenant_001",
  "request_id": "req_20260606_0464",
  "session_id": "sess_015",
  "user_id_hash": "usr_015",
  "query": {
    "text": "smartwatch with gps",
    "normalized_text": "smartwatch gps",
    "filters": {},
    "sort": null
  },
  "response": {
    "status_code": 503,
    "latency_ms": 11572,
    "result_count": 0,
    "results": []
  },
  "interaction": {
    "clicks": [],
    "cart_adds": []
  },
  "context": {
    "device_type": "tablet",
    "channel": "web",
    "locale": "en-US"
  },
  "error": "provider_error"
}
```
