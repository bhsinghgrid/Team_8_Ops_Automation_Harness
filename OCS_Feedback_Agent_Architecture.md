# OCS Feedback Agent — Architecture & Workflow

> Architecture and workflow diagrams for the **Feedback Agent** in the Magellan OCSS Ops Harness pipeline, adapted for [Open Commerce Search Stack](https://github.com/CommerceExperts/open-commerce-search).

---

## 1. System Context — Where the Feedback Agent Fits

The Feedback Agent sits at the **end of the sequential pipeline**, after the FixPlanAgent has applied its changes to the OCS stack. It closes the loop by verifying, measuring, deciding, and learning.

```mermaid
graph LR
    subgraph Upstream Pipeline
        A["User / Channel<br/><i>query: hybrid work backpack</i>"] --> B["Search API / Gateway"]
        B --> C["OCS Search Engine<br/><i>Elasticsearch + Querqy</i>"]
        C --> D["Observability Layer<br/><i>query logs, metrics</i>"]
        D --> E["Signal Detection<br/><i>zero-result, drift</i>"]
        E --> F["Diagnosis<br/><i>CapabilityImpact,<br/>MetricImpact,<br/>DataGapRuleDiff</i>"]
        F --> G["Runbook / Fix Plan<br/><i>FixPlanAgent</i>"]
    end

    subgraph Release Phase
        G --> H["Human Approval<br/><i>optional gate</i>"]
        H --> I["Apply Fix<br/><i>applyResult: ok</i>"]
    end

    subgraph Feedback Loop
        I --> J["🔄 FEEDBACK AGENT<br/><i>verify → measure → decide</i>"]
        J -->|PROMOTE| K["Search Config Update<br/><i>OCS Config Service</i>"]
        J -->|ROLLBACK| L["Release Controller<br/><i>revert patches</i>"]
        J -->|threshold updates| M["PostgreSQL / Audit<br/><i>watchlists, thresholds</i>"]
        M -.->|"learning loop"| E
        K --> N["Canary Workflow<br/><i>5% → 25% → 100%</i>"]
    end

    style J fill:#7A2E1E,color:#F2EDE1,stroke:#D4A017,stroke-width:3px
    style M fill:#265D6B,color:#F2EDE1
    style K fill:#3D4A2E,color:#F2EDE1
    style L fill:#B8860B,color:#0F0E0C
```

---

## 2. Feedback Agent — Internal Architecture

The agent is composed of **5 sub-agents**, each responsible for a phase of the feedback loop.

```mermaid
graph TB
    INPUT["📥 input.json<br/><i>FixPlanAgent output</i>"] --> FA

    subgraph FA["Feedback Agent"]
        direction TB

        FV["1️⃣ FixVerificationAgent<br/>─────────────<br/>• Parse applyResult<br/>• Re-execute query vs OCS Search API<br/>• Verify catalog patch in Config Service<br/>• Verify synonyms active in Querqy<br/>• Verify embedding refresh in Indexer<br/>• Verify merchandising rules applied"]

        MC["2️⃣ MetricComparisonAgent<br/>─────────────<br/>• Collect baseline from expectedOutcome<br/>• Collect live metrics from OCS telemetry<br/>• Compute CTR, latency, relevance deltas<br/>• Check zero-result rate reduction<br/>• Statistical significance test"]

        CE["3️⃣ CanaryEvaluationAgent<br/>─────────────<br/>• Review shadow test results (s2n=6.0)<br/>• Evaluate candidate vs primary diffs<br/>• Check business guardrails<br/>• Generate PROMOTE / ROLLBACK / HOLD"]

        TU["4️⃣ ThresholdUpdateAgent<br/>─────────────<br/>• Update query cluster watchlist<br/>• Patch runbook templates<br/>• Adjust detection sensitivity<br/>• Update approval routing"]

        AT["5️⃣ AuditTrailAgent<br/>─────────────<br/>• Write immutable audit record<br/>• Link evidence chain<br/>• Store rollback plan status<br/>• Archive fix artifacts"]

        FV --> MC --> CE --> TU --> AT
    end

    AT --> OUTPUT["📤 feedback_result.json"]

    style FA fill:#1B1A18,color:#F2EDE1,stroke:#7A2E1E,stroke-width:2px
    style FV fill:#7A2E1E,color:#F2EDE1
    style MC fill:#265D6B,color:#F2EDE1
    style CE fill:#B8860B,color:#0F0E0C
    style TU fill:#3D4A2E,color:#F2EDE1
    style AT fill:#0F0E0C,color:#F2EDE1,stroke:#6B6558
```

---

## 3. End-to-End Workflow Flowchart

```mermaid
flowchart TD
    START(["🟢 Fix Applied<br/>applyResult.applied = true"]) --> PARSE["Parse input.json<br/>Extract: query, fixOrder,<br/>patches, expectedOutcome"]

    PARSE --> V1{"All verification<br/>checks passed?"}

    V1 -->|No| VFAIL["❌ Log verification failure<br/>Mark patches as NOT_APPLIED"]
    VFAIL --> ROLLBACK_IMMEDIATE["🔴 Immediate Rollback<br/>Revert all patches"]
    ROLLBACK_IMMEDIATE --> AUDIT_FAIL["Write audit: VERIFICATION_FAILED"]

    V1 -->|Yes| REQUERY["Re-execute incident query<br/>POST /search-api/v1/search<br/>q=hybrid work backpack"]

    REQUERY --> RESULTS{"Results > 0?<br/>(was 0 before fix)"}

    RESULTS -->|No| PARTIAL["⚠️ Partial Fix<br/>Some patches may have failed"]
    PARTIAL --> HUMAN_REVIEW["Request Human Review<br/>HOLD decision"]

    RESULTS -->|Yes| METRICS["Collect Live Metrics<br/>• zero-result rate<br/>• CTR<br/>• latency p50/p95<br/>• conversion rate"]

    METRICS --> COMPARE["Compare Against Baseline<br/>expectedOutcome.metrics"]

    COMPARE --> DEGRADED{"Any critical metric<br/>degraded > threshold?"}

    DEGRADED -->|Yes| ROLLBACK["🔴 ROLLBACK<br/>Revert via OCS Config Service"]
    ROLLBACK --> AUDIT_ROLL["Write audit: ROLLED_BACK"]

    DEGRADED -->|No| CANARY["Evaluate Canary Results<br/>shadow_test s2n = 6.0"]

    CANARY --> SIGNIFICANT{"Statistically<br/>significant<br/>improvement?"}

    SIGNIFICANT -->|No| HOLD["🟡 HOLD<br/>Extend monitoring window"]
    HOLD --> HUMAN_REVIEW

    SIGNIFICANT -->|Yes| PROMOTE["🟢 PROMOTE<br/>Advance to next traffic tier<br/>5% → 25% → 100%"]

    PROMOTE --> UPDATE["Update Feedback Loop State"]
    HOLD --> UPDATE
    ROLLBACK --> UPDATE
    HUMAN_REVIEW --> UPDATE

    UPDATE --> WATCHLIST["Update query cluster watchlist<br/>• Add to resolved incidents<br/>• Set 7-day monitoring"]
    WATCHLIST --> THRESHOLDS["Update detection thresholds<br/>• autocomplete_miss sensitivity<br/>• stale_embedding sensitivity"]
    THRESHOLDS --> TEMPLATES["Update runbook templates<br/>• Record successful fix pattern<br/>• Store duration metrics"]
    TEMPLATES --> ROUTING["Update approval routing<br/>• Record owner path<br/>• Escalation patterns"]

    ROUTING --> AUDIT_OK["📋 Write Audit Record<br/>• Incident ID, timestamp<br/>• Fix order, patches<br/>• Metric deltas<br/>• Decision + confidence<br/>• Evidence chain"]

    AUDIT_OK --> END(["🏁 Feedback Cycle Complete"])

    style START fill:#3D4A2E,color:#F2EDE1
    style PROMOTE fill:#3D4A2E,color:#F2EDE1
    style ROLLBACK fill:#7A2E1E,color:#F2EDE1
    style HOLD fill:#B8860B,color:#0F0E0C
    style HUMAN_REVIEW fill:#B8860B,color:#0F0E0C
    style END fill:#265D6B,color:#F2EDE1
```

---

## 4. Sequence Diagram — Sub-Agent ↔ OCS Component Interactions

```mermaid
sequenceDiagram
    participant IN as input.json
    participant FV as FixVerificationAgent
    participant MC as MetricComparisonAgent
    participant CE as CanaryEvaluationAgent
    participant TU as ThresholdUpdateAgent
    participant AT as AuditTrailAgent
    participant OCS as OCS Search API
    participant IDX as Indexer Service
    participant SUG as Suggest Service
    participant CFG as Config Service
    participant ES as Elasticsearch
    participant PG as PostgreSQL/Audit

    Note over IN,AT: Phase 1 — Fix Verification (~5 min)
    IN->>FV: applyResult, patches, fixOrder
    FV->>OCS: POST /search-api/v1/search {q: "hybrid work backpack"}
    OCS-->>FV: results[] (expect > 0)
    FV->>CFG: GET /config/searchable-fields
    CFG-->>FV: fields[] (expect description, tags, terrain, waterproof)
    FV->>OCS: POST /search {q: "professional backpack"} (synonym test)
    OCS-->>FV: results[] (expect matches via synonym)
    FV->>IDX: GET /indexer/status/{sku-backpack-1}
    IDX-->>FV: embedding timestamp (expect aligned)
    FV->>OCS: GET /search-api/v1/rules/active
    OCS-->>FV: rules[] (expect 3 merchandising rules)

    Note over FV,MC: Phase 2 — Metric Comparison (~10 min)
    FV->>MC: verification_report (all_passed: true/false)
    MC->>OCS: POST /search (incident query request)
    OCS-->>MC: query results, scores, X-Search-Time header
    MC->>MC: compute deltas & dynamic relevance score vs expectedOutcome.metrics

    Note over MC,CE: Phase 3 — Canary Evaluation (~15 min)
    MC->>CE: metric_deltas, live_metrics
    CE->>CE: Review shadow_test (s2n=6.0, candidateDiffs=5, noiseDiffs=1)
    CE->>CE: Apply business guardrails
    CE->>CE: Generate decision: PROMOTE | ROLLBACK | HOLD

    Note over CE,TU: Phase 4 — Threshold Update (~5 min)
    CE->>TU: decision, evidence_chain
    TU->>CFG: PATCH /config/watchlists
    CFG-->>TU: updated
    TU->>PG: UPDATE thresholds SET autocomplete_miss=adjusted
    PG-->>TU: ok
    TU->>PG: INSERT runbook_template_patch
    PG-->>TU: ok

    Note over TU,AT: Phase 5 — Audit Trail (~2 min)
    TU->>AT: all outputs
    AT->>PG: INSERT audit_record (incident_id, query, gap_type, fix_order, metric_deltas, decision, confidence, evidence_artifacts)
    PG-->>AT: record_id
    AT->>IN: feedback_result.json
```

---

## 5. State Machine — Feedback Loop Lifecycle

```mermaid
stateDiagram-v2
    [*] --> FixApplied: applyResult.applied = true

    FixApplied --> Verifying: Start verification checks
    Verifying --> VerificationFailed: Any check fails
    Verifying --> Verified: All 5 checks pass

    VerificationFailed --> RolledBack: Immediate rollback

    Verified --> Measuring: Collect live metrics
    Measuring --> Measured: Deltas computed

    Measured --> Deciding: Apply guardrails

    Deciding --> Promoted: All metrics positive + significant
    Deciding --> RolledBack: Critical metric degraded
    Deciding --> Held: Inconclusive / needs human review

    Promoted --> Learning: Update thresholds
    RolledBack --> Learning: Record failure pattern
    Held --> HumanReview: Await operator decision
    HumanReview --> Promoted: Operator approves
    HumanReview --> RolledBack: Operator rejects

    Learning --> Auditing: Write audit record
    Auditing --> Closed: Cycle complete

    Closed --> [*]

    note right of Promoted
        Advance canary traffic
        5% → 25% → 50% → 100%
    end note

    note right of Learning
        Update watchlists, thresholds,
        runbook templates, routing
    end note

    note right of RolledBack
        Revert all patches via
        OCS Config Service
    end note
```

---

## 6. Data Flow — input.json → Sub-Agent Mapping

Shows which fields from `input.json` flow to which sub-agent.

```mermaid
graph LR
    subgraph INPUT["input.json"]
        Q["query<br/><i>hybrid work backpack</i>"]
        IP["issueProfile<br/><i>gapType, signals,<br/>searchableFields</i>"]
        CP["catalogPatch<br/><i>fields, weights,<br/>catalogSize</i>"]
        EP["embeddingPatch<br/><i>refreshEmbeddings,<br/>affectedProductIds</i>"]
        AP["autocompletePatch<br/><i>synonymMappings,<br/>evidence</i>"]
        MP["merchandisingPatch<br/><i>rules, boost,<br/>conditions</i>"]
        EO["expectedOutcome<br/><i>metrics, searchResults</i>"]
        VR["verification<br/><i>checks[]</i>"]
        AR["applyResult<br/><i>artifacts,<br/>appliedSearchConfig</i>"]
        RS["rlmSynthesis<br/><i>shadow_test,<br/>confidence, windows</i>"]
    end

    Q --> FV
    VR --> FV
    AR --> FV
    CP --> FV
    EP --> FV
    AP --> FV
    MP --> FV

    EO --> MC
    IP --> MC

    RS --> CE

    IP --> TU

    Q --> AT
    IP --> AT
    AR --> AT

    subgraph AGENTS["Feedback Sub-Agents"]
        FV["1. FixVerificationAgent"]
        MC["2. MetricComparisonAgent"]
        CE["3. CanaryEvaluationAgent"]
        TU["4. ThresholdUpdateAgent"]
        AT["5. AuditTrailAgent"]
    end

    style INPUT fill:#1B1A18,color:#F2EDE1
    style AGENTS fill:#2A2621,color:#F2EDE1
    style FV fill:#7A2E1E,color:#F2EDE1
    style MC fill:#265D6B,color:#F2EDE1
    style CE fill:#B8860B,color:#0F0E0C
    style TU fill:#3D4A2E,color:#F2EDE1
    style AT fill:#0F0E0C,color:#F2EDE1,stroke:#6B6558
```

---

## 7. OCS Component Mapping (Magellan → OCS)

How the Feedback Agent replaces Magellan's proprietary AI search engine with Open Commerce Search Stack components:

| Magellan Concept | OCS Replacement | API Endpoint |
|-----------------|-----------------|--------------|
| AI Search Engine | **OCS Search API** | `POST /search-api/v1/search` |
| Embedding Refresh | **Indexer Service** | `POST /indexer-service/v1/full-index` |
| Synonym / Autocomplete | **Suggest Service** + **Querqy** | `GET /suggest-service/v1/suggest` |
| Searchable Fields Config | **Config Service** | `GET/PUT /config-service/v1/index-config` |
| Merchandising Rules | **Querqy rules** via Search Service | Querqy rule files in config |
| A/B / Shadow Testing | OCS with **traffic routing** | Custom header-based routing |
| Observability | **OCS Search Response Headers** (e.g. `X-Search-Time`) + HTTP round-trip telemetry | Search response headers & metadata |
| Audit / Persistence | **PostgreSQL** | Direct JDBC/connection |

---

## 8. Output Schema — `feedback_result.json`

```json
{
  "agent": "FeedbackAgent",
  "status": "ok",
  "query": "hybrid work backpack",
  "timestamp": "2026-06-03T17:30:00+05:30",
  "verification": {
    "allPassed": true,
    "checks": [
      {"name": "query_returns_results", "passed": true, "resultCount": 3},
      {"name": "searchable_fields_applied", "passed": true, "fieldsAdded": 4},
      {"name": "synonyms_active", "passed": true, "mappingsVerified": 3},
      {"name": "embedding_refreshed", "passed": true, "productsRefreshed": 1},
      {"name": "merchandising_rules_applied", "passed": true, "rulesApplied": 3}
    ]
  },
  "metrics": {
    "zeroResultRate": {"before": 1.0, "after": 0.0, "delta": -1.0},
    "ctr": {"before": 0, "after": "pending_canary", "delta": "n/a"},
    "latency_p95_ms": {"before": 45, "after": 52, "delta": +7},
    "relevanceScore": {"before": 0, "after": 0.82, "delta": +0.82}
  },
  "decision": {
    "action": "PROMOTE",
    "confidence": 0.577,
    "reason": "All verification checks passed. Zero-result rate eliminated. Latency within acceptable bounds. Shadow test s2n=6.0 indicates strong signal.",
    "nextTrafficTier": "25%"
  },
  "thresholdUpdates": {
    "watchlistAdded": "hybrid work backpack",
    "monitoringWindow": "7d",
    "regressionThreshold": "zero_result_rate > 0.05",
    "runbookTemplatePatched": true,
    "signalSensitivityAdjusted": ["autocomplete_miss", "stale_embedding"]
  },
  "auditRecord": {
    "incidentId": "INC-20260603-001",
    "gapType": "query_vocabulary_gap",
    "fixOrderExecuted": 5,
    "patchesApplied": 4,
    "evidenceArtifacts": 7,
    "ownerPath": "Application owner",
    "rollbackAvailable": true
  }
}
```

---

## 9. Deployment Notes

> [!TIP]
> To run the OCS stack locally for development, follow the [OCSS Quick Start Demo](https://commerceexperts.github.io/open-commerce-search/quick_start_demo.html). The feedback agent should be configured with base URLs for:
> - Search API: `http://localhost:8534`
> - Indexer Service: `http://localhost:8535`
> - Config Service: `http://localhost:8536`
> - Elasticsearch: `http://localhost:9200`
