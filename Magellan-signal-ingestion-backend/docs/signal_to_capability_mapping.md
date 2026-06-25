# Signal to Capability Mapping

This document outlines how the raw operational signals detected by the Magellan AI Search Ops Harness map to specific Grid Dynamics AI Search capabilities. This mapping occurs during the "Diagnosis" phase (Step 2 of the Ops Flow) and dictates which runbooks are subsequently generated.

The current implementation detects six primary signals across log consumption and state snapshots.

## 1. Log-Based Signals (From Search Logs)

These signals are detected by analyzing tumbling windows of ingested search logs.

### `latency_spike` (High P95 Latency)
*   **Trigger:** The 95th percentile latency of search responses within a window exceeds the configured threshold (e.g., > 150ms).
*   **Primary Responsible Capabilities:** **Semantic Vector Search** & **MXP Merchandising Rules**
*   **Diagnosis Context:** 
    *   *Semantic Search:* The vector database may be overloaded, or dense queries are unoptimized.
    *   *MXP Rules:* Complex post-retrieval filters, heavy synonym expansions, or numerous active campaigns are bogging down the response time.

### `zero_results` (High Zero-Result Rate)
*   **Trigger:** The rate of successful search queries returning zero products exceeds the configured threshold.
*   **Primary Responsible Capabilities:** **Semantic Vector Search** & **Catalog Optimization**
*   **Secondary Impact:** **Smart Autocomplete**
*   **Diagnosis Context:** The engine failed to match user intent to inventory.
    *   *Catalog Optimization:* Are products missing entirely, or are crucial attributes (e.g., "waterproof") missing?
    *   *Semantic Search:* Is the vector model failing to bridge the semantic gap between the query and the product descriptions?
    *   *Autocomplete:* Is the autocomplete suggesting "dead-end" prefixes that guarantee zero results?

### `low_ctr` (Click-Through Rate Drop)
*   **Trigger:** The Click-Through Rate (CTR) for successful searches drops below the configured threshold (e.g., < 5%).
*   **Primary Responsible Capabilities:** **Semantic Vector Search** & **Personalized Results**
*   **Secondary Impact:** **Smart Autocomplete**
*   **Diagnosis Context:** Search yields results, but relevance is poor (users abandon the page).
    *   *Semantic Search:* The retrieved results don't align with the actual user intent.
    *   *Personalization:* The engine is failing to match brand preferences or session behavior.
    *   *Autocomplete:* Users selected a suggested prefix, but the resulting page did not meet their expectations (as outlined in Scenario B: "Autocomplete Misses a Demand Trend").

### `error_rate` (HTTP 4xx/5xx Errors)
*   **Trigger:** The rate of HTTP errors or explicit error messages in the search logs exceeds the threshold.
*   **Primary Responsible Capability:** **Multimodal Search** & **Core Infrastructure**
*   **Diagnosis Context:** 
    *   *Multimodal Search:* A spike in 400 (Bad Request) or 500 (Internal Error) can indicate failures parsing voice transcripts or image payloads.
    *   *Infrastructure:* Represents generic backend timeouts (504) or service unavailability (503).

---

## 2. Snapshot-Based Signals (From Change Detection Agent)

These signals are detected by comparing hash digests of incoming state payloads against the previously known state.

### `CATALOG_DELTA` (Catalog Snapshot Change)
*   **Trigger:** A newly ingested catalog snapshot differs from the previously stored snapshot.
*   **Primary Responsible Capability:** **Catalog Optimization**
*   **Secondary Impact:** **Semantic Vector Search**
*   **Diagnosis Context:** Maps directly to Scenario A ("Catalog Update Breaks Semantic Retrieval"). The arrival of new products or modified attributes triggers a check for catalog completeness (gaps) and flags Semantic Search because the new data likely requires a "Semantic Index Refresh" (re-embedding).

### `MXP_RULE_DIFF` (Merchandising Rule Change)
*   **Trigger:** A newly ingested Merchandising (MXP) rule snapshot differs from the previously stored snapshot.
*   **Primary Responsible Capability:** **MXP Merchandising Rules**
*   **Diagnosis Context:** Maps directly to Scenario C ("Merchandising Rule Conflict"). A rule change triggers a diagnostic check to ensure new campaign boosts aren't suppressing higher-converting substitutes or creating logic conflicts.
