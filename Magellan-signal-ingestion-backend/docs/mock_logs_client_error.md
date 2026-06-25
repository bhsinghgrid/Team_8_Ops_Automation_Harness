# Client Errors in Mock Search Logs

This document provides examples of search log entries from `mock-data/logs/search_events.jsonl` that represent client-side errors. These typically manifest as HTTP `400 Bad Request` status codes and an `error` field set to `"client_error"`.

Client errors indicate issues originating from the search request itself, such as malformed queries or invalid parameters sent by the client.

---

## Example 1: Empty Query

This log simulates a client sending an empty query, which the search service rejects as a bad request.

```json
{
  "timestamp": "2026-06-06T11:15:10Z",
  "source": "gd_ai_search",
  "tenant": "retail_tenant_001",
  "request_id": "req_20260606_0451",
  "session_id": "sess_002",
  "user_id_hash": "usr_002",
  "query": {
    "text": "",
    "normalized_text": null,
    "filters": {},
    "sort": null
  },
  "response": {
    "status_code": 400,
    "latency_ms": 11273,
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
  "error": "client_error"
}
```

---

## Example 2: Malformed Filter Payload

This log represents a scenario where the client's request included a malformed or syntactically incorrect filter payload, leading to a bad request error.

```json
{
  "timestamp": "2026-06-06T11:15:20Z",
  "source": "gd_ai_search",
  "tenant": "retail_tenant_001",
  "request_id": "req_20260606_0452",
  "session_id": "sess_003",
  "user_id_hash": "usr_003",
  "query": {
    "text": "%%%% malformed filter payload",
    "normalized_text": "malformed filter payload",
    "filters": {},
    "sort": null
  },
  "response": {
    "status_code": 400,
    "latency_ms": 11296,
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
  "error": "client_error"
}
```
