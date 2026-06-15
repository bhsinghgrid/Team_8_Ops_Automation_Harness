# Timeout Errors in Mock Search Logs

This document provides examples of search log entries from `mock-data/logs/search_events.jsonl` that represent timeout errors. These are typically characterized by HTTP `504 Gateway Timeout` status codes and an `error` field set to `"timeout"`.

Timeout errors indicate that the search service, or a downstream dependency it relies on, failed to respond within a configured time limit.

---

## Example 1: Search Service Timeout

This log simulates a valid search query timing out, resulting in a 504 status code.

```json
{
  "timestamp": "2026-06-06T11:15:30Z",
  "source": "gd_ai_search",
  "tenant": "retail_tenant_001",
  "request_id": "req_20260606_0453",
  "session_id": "sess_004",
  "user_id_hash": "usr_004",
  "query": {
    "text": "waterproof hiking boots",
    "normalized_text": "waterproof hiking boots",
    "filters": {
      "waterproof": "true"
    },
    "sort": null
  },
  "response": {
    "status_code": 504,
    "latency_ms": 11319,
    "result_count": 0,
    "results": []
  },
  "interaction": {
    "clicks": [],
    "cart_adds": []
  },
  "context": {
    "device_type": "desktop",
    "channel": "web",
    "locale": "en-US"
  },
  "error": "timeout"
}
```

---

## Example 2: Another Search Timeout

Another instance of a search query encountering a timeout.

```json
{
  "timestamp": "2026-06-06T11:16:20Z",
  "source": "gd_ai_search",
  "tenant": "retail_tenant_001",
  "request_id": "req_20260606_0458",
  "session_id": "sess_009",
  "user_id_hash": "usr_009",
  "query": {
    "text": "waterproof hiking boots",
    "normalized_text": "waterproof hiking boots",
    "filters": {
      "waterproof": "true"
    },
    "sort": null
  },
  "response": {
    "status_code": 504,
    "latency_ms": 11434,
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
  "error": "timeout"
}
```
