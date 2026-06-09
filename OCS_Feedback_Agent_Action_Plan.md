# OCS Feedback Agent — Action Plan

## 1. Problem Statement

The **Magellan OCSS Ops Harness** (documented in [Magellan-Backend-Automator.html](file:///Users/hsrivastava/Desktop/feedback_agent/Magellan-Backend-Automator.html)) defines an ops automation control plane around the **Open Commerce Search Stack (OCSS)**. The task is to build the **Feedback Agent** — the component that closes the loop after a fix has been planned, applied, and its results observed.

The agent receives a structured [input.json](file:///Users/hsrivastava/Desktop/feedback_agent/input.json) (output from the upstream FixPlanAgent pipeline) and must:
1. Validate the fix was applied correctly
2. Measure the impact against baseline metrics
3. Determine if the fix should be promoted, rolled back, or iterated
4. Update watchlists, thresholds, and runbook templates for future cycles

---

## 2. Understanding the Input Contract

The `input.json` represents the **complete output of a sequential agent pipeline** that has already:

| Stage | Agent | Purpose |
|-------|-------|---------|
| 1 | `CapabilityImpactAgent` | Ranks affected OCSS capabilities (e.g., merchandising_governance) |
| 2 | `MetricImpactAgent` | Checks relevance, CTR, latency metrics (2/3 failed in sample) |
| 3 | `DataGapRuleDiffAgent` | Identifies gap type (`query_vocabulary_gap`, confidence: high) |
| 3s | `ShadowTestAgent` | Diffy-style candidate-vs-primary comparison (s2n=6.0) |
| 4 | `OwnerPathAgent` | Routes to primary owner with 5 escalation routes |
| 5 | `IncidentWorkAIAgent` | Synthesizes evidence into incident brief |
| 6 | `FixPlanAgent` | Generates fix order + patches (catalog, embedding, autocomplete, merchandising) |
| 7 | `RMLSynthesisAgent` | Folds evidence back into parent incident context |

**The Feedback Agent starts where this pipeline ends** — after `applyResult.applied = true`.

---

## 3. What the Feedback Agent Must Do

### 3.1 Core Responsibilities

```
┌─────────────────────────────────────────────────────────┐
│                   FEEDBACK AGENT                         │
│                                                         │
│  INPUT: FixPlanAgent output (input.json)                │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Verify Fix  │→ │ Measure      │→ │ Decide       │  │
│  │  Application │  │ Impact       │  │ Promote/Roll │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                 │                 │           │
│         ▼                 ▼                 ▼           │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Update Feedback Loop State             │  │
│  │  (watchlists, thresholds, runbook templates)     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  OUTPUT: feedback_result.json                           │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Sub-Agent Breakdown

| Sub-Agent | Input | Output | OCS API Touchpoint |
|-----------|-------|--------|--------------------|
| **FixVerificationAgent** | `applyResult`, `appliedSearchConfiguration` | Verification report: which patches succeeded, which failed | OCS Search API `/search-api/v1/search` |
| **MetricComparisonAgent** | `expectedOutcome.metrics`, live OCS telemetry | Before/after metric deltas (CTR, latency, relevance, recall) | OCS Search API, Elasticsearch `_stats` |
| **CanaryEvaluationAgent** | Shadow test results, metric deltas | Statistical significance, promotion/rollback recommendation | OCS Search API with A/B routing |
| **ThresholdUpdateAgent** | Decision + historical patterns | Updated watchlists, thresholds, runbook template patches | Config Service API |
| **AuditTrailAgent** | All above outputs | Immutable audit record with evidence chain | PostgreSQL / Audit Ledger |

---

## 4. Mapping to Open Commerce Search (OCS) APIs

> [!IMPORTANT]
> Unlike Magellan (which wraps a proprietary AI search engine), this agent targets the [Open Commerce Search Stack](https://github.com/CommerceExperts/open-commerce-search). The key OCS components the feedback agent interacts with:

| OCS Component | Feedback Agent Interaction |
|---------------|---------------------------|
| **OCS Search API** (`search-service`) | Re-execute the original query to verify fix impact; compare result sets before/after |
| **Indexer Service** (`indexer-service`) | Verify embedding refresh completed; check index timestamps align |
| **Suggest Service** (`suggest-service-parent`) | Verify synonym mappings are active; test autocomplete for affected terms |
| **Querqy** (via search-service) | Verify merchandising rules applied; check for rule conflicts |
| **Config Service** (`config-service`) | Read/write searchable field configs, synonym mappings |
| **Elasticsearch** (backend) | Check shard health, index freshness, mapping updates |

---

## 5. Detailed Action Plan (Status: COMPLETED)

### Phase 1: Fix Verification
- [x] **Parse `applyResult`** from input.json
  - Confirm `applied: true` and `dryRun: false`
  - Walk the `artifacts[]` array to locate each patch file
  - Verify each `verification.checks[]` passed
- [x] **Re-execute the incident query against OCS Search API**
  - Query: `"hybrid work backpack"` (from `input.json.query`)
  - Endpoint: `POST /search-api/v1/search`
  - Compare: `expectedOutcome.searchResults.before` (0) vs actual result count
  - Verify: `searchableFields` now include `description`, `tags`, `terrain`, `waterproof`
- [x] **Verify catalog patch applied**
  - Check that the 4 new searchable fields exist in OCS Config Service
  - Confirm field weights match (`description: 0.75`, `tags: 0.85`, etc.)
- [x] **Verify synonym mappings active**
  - Test each synonym mapping (`hybrid → professional, bag, laptop, office`)
  - Execute OCS search with synonym terms and confirm broader recall
- [x] **Verify embedding refresh**
  - Check `affectedProductIds: ["sku-backpack-1"]` was re-embedded
  - Compare embedding timestamps with catalog timestamps
- [x] **Verify merchandising rules**
  - Confirm 3 rules applied: `rule-promote-in-stock`, `rule-boost-relevant`, `rule-conflict-guard`
  - Verify `mxp-rule-campaign-boost` is suppressed

### Phase 2: Metric Comparison
- [x] **Collect baseline metrics** from `expectedOutcome.metrics`
  - CTR: expected lift
  - Latency: stable after change
  - Relevance: improved with broader coverage
  - Semantic recall: stale → refreshed
- [x] **Collect live metrics** from OCS telemetry
  - Zero-result rate for the affected query cluster
  - CTR for search results page
  - Latency p50/p95 from search response headers / gateway round-trip time
  - Conversion rate (if available from analytics pipeline)
- [x] **Compute deltas and statistical significance**
  - Use the `ShadowTestAgent` baseline: `s2n = 6.0` (signal-to-noise ratio)
  - Minimum sample: 100 queries for statistical significance
  - Alert if any metric degrades beyond threshold

### Phase 3: Canary Evaluation & Decision
- [x] **Review shadow test results** from `rlmSynthesis.workAiWindows.shadow_test`
  - `candidateResponseDiffCount: 5` (real signal)
  - `noiseResponseDiffCount: 1` (noise baseline)
  - `signalToNoiseRatio: 6.0` (strong signal)
- [x] **Make promotion/rollback decision**
  - Check S2N rules: Promote if >= 5.0, Hold if >= 2.0, Rollback if < 2.0.
  - Enforce latency guardrails: rollback if degradation is > 25% or > 15ms.
- [x] **Generate decision report** with:
  - Decision: `PROMOTE | ROLLBACK | HOLD`
  - Confidence score (from RMLSynthesis: `0.577`)
  - Evidence chain linking signal → diagnosis → fix → verification
  - Affected products and queries

### Phase 4: Threshold & Watchlist Update
- [x] **Update query cluster watchlist**
  - Add `"hybrid work backpack"` to resolved incidents
  - Set monitoring window: 7 days post-fix
  - Define regression threshold: if zero-result rate returns > 5%
- [x] **Update runbook templates**
  - Record that `query_vocabulary_gap` with `high` confidence was successfully remediated.
  - Dynamically parse and sum up durations from `result.implementation.phases` (1535 min).
- [x] **Update approval routing**
  - Record that `Application owner` was the primary owner for this incident type
- [x] **Update detection thresholds**
  - Adjust sensitivity for `autocomplete_miss` and `stale_embedding` signals

### Phase 5: Audit Trail
- [x] **Write audit record** to PostgreSQL / SQLite Audit Ledger
  - Incident ID (parsed from `artifactDir` or fall back to system timestamp), timestamp, query, gap type
  - Fix order executed, verification results, metric deltas, decision, confidence, and owner details

---

## 6. Resolved Decisions

- **OCS Deployment Target**: Configured for dual-mode running. Defaults to **Mock/Simulated Mode** for sandbox testing and validation, and switches to **Live Mode** connecting to configured endpoint URLs via environment variables.
- **Metric Collection**: Shifted from querying internal Elasticsearch `_nodes/stats` admin ports (often firewalled) to gateway-level telemetry. Evaluates round-trip HTTP search request latency and inspects response headers (`X-Search-Time` / `X-OCS-Latency`) and dynamic relevance overlaps.
- **Persistence Layer**: Implemented `db.py` supporting PostgreSQL connections, with automatic graceful fallback to a local SQLite instance (`ocs_feedback.db`) for immediate workspace testing.
- **Agent Framework**: Implemented as a modular Python package (`feedback_agent/`) orchestrating five sequential sub-agents (`FixVerificationAgent`, `MetricComparisonAgent`, `CanaryEvaluationAgent`, `ThresholdUpdateAgent`, and `AuditTrailAgent`) executing in order.

---

## 7. Verification Plan

### Automated Tests
- [x] Executed integration test running the whole pipeline:
  ```bash
  python3 -m feedback_agent.main --input input.json --output feedback_result.json
  ```
- [x] Verified output `feedback_result.json` schema correctness.
- [x] Confirmed SQLite database schema tables are correctly created and updated.

### Manual Verification
- [x] Verified zero-result query transitions to results.
- [x] Verified database logs.

