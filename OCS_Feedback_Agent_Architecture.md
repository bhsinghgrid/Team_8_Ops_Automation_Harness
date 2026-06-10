# OCS Feedback Agent — Architecture & Workflow

> Architecture and workflow diagrams for the **Feedback Agent** and the **Canary Release Controller** in the Magellan OCSS Ops Harness pipeline, adapted for [Open Commerce Search Stack](https://github.com/CommerceExperts/open-commerce-search).

---

## 1. System Context — Where the Canary and Feedback Agent Fit

The **Canary Release Controller** orchestrates the rollout phase of search configuration changes, executing progressive traffic weight steps ($5\% \rightarrow 25\% \rightarrow 50\% \rightarrow 100\%$). At each step, it triggers the **Feedback Agent** to verify, measure, and evaluate the candidate configuration, automatically promoting the tier, rolling back all modifications on regressions, or pausing for human review.

```mermaid
graph TD
    subgraph Upstream & Diagnosis
        A["User / Channel<br/><i>query: hybrid work backpack</i>"] --> B["Search API / Gateway"]
        B --> C["OCS Search Engine<br/><i>Elasticsearch + Querqy</i>"]
        C --> D["Observability Layer<br/><i>telemetry metrics</i>"]
        D --> E["Signal Detection<br/><i>zero-result, drift</i>"]
        E --> F["Diagnosis Agent<br/><i>runbook selection</i>"]
        F --> G["Fix Plan Agent<br/><i>Produces input.json</i>"]
    end

    subgraph Governed Release Ops (Phase 4)
        G --> H["Canary Release Controller<br/><i>canary/controller.py</i>"]
        H -->|1. Route Traffic| I["OCS Config Service<br/><i>traffic_router.py (5%, 25%, 50%, 100%)</i>"]
        I -->|2. Invoke Pipeline| J["🔄 Feedback Agent Pipeline<br/><i>main.py</i>"]
        J -->|3. Evaluate Decision| K{"Feedback Decision?"}
        K -->|PROMOTE| L{"All Tiers Completed?"}
        L -->|No| H
        L -->|Yes| M["Release Finalized<br/><i>COMPLETED (100% Traffic)</i>"]
        
        K -->|ROLLBACK| N["Revert Config & Reset Traffic<br/><i>rollback.py (0% Traffic)</i>"]
        N --> O["Mark status: ROLLED_BACK"]
        
        K -->|HOLD| P["Pause Progression<br/><i>Max holds check / Human review</i>"]
        P --> Q["Mark status: HELD"]
    end

    subgraph Database & Learning (Phase 3)
        J -->|4. Threshold Updates| R["PostgreSQL / SQLite<br/><i>watchlists, runbooks, sensitivities</i>"]
        R -.->|"learning loop"| E
    end

    style H fill:#7A2E1E,color:#F2EDE1,stroke:#D4A017,stroke-width:2px
    style J fill:#265D6B,color:#F2EDE1,stroke:#D4A017,stroke-width:2px
    style R fill:#3D4A2E,color:#F2EDE1
    style N fill:#B8860B,color:#0F0E0C
```

---


## 2. Feedback Agent — Internal Architecture

The Feedback Agent is composed of **5 sub-agents** orchestrated sequentially to analyze the applied configuration at the current canary traffic tier:

```mermaid
graph TB
    CANARY["Canary Release Controller<br/><i>canary/controller.py</i>"] -->|input.json| FA
 
    subgraph FA["Feedback Agent Pipeline"]
        direction TB

        FV["1️⃣ FixVerificationAgent<br/>─────────────<br/>• Parse applyResult<br/>• Re-execute query vs OCS Search API<br/>• Verify catalog patch in Config Service<br/>• Verify synonyms active in Querqy<br/>• Verify embedding refresh in Indexer<br/>• Verify merchandising rules applied"]

        MC["2️⃣ MetricComparisonAgent<br/>─────────────<br/>• Collect baseline from expectedOutcome<br/>• Collect live metrics from OCS telemetry<br/>• Compute CTR, latency, relevance deltas<br/>• Check zero-result rate reduction<br/>• Statistical significance test"]

        CE["3️⃣ CanaryEvaluationAgent<br/>─────────────<br/>• Review shadow test results (s2n=6.0)<br/>• Evaluate candidate vs primary diffs<br/>• Check business guardrails<br/>• Generate PROMOTE / ROLLBACK / HOLD"]

        TU["4️⃣ ThresholdUpdateAgent<br/>─────────────<br/>• Update query cluster watchlist<br/>• Patch runbook templates<br/>• Adjust detection sensitivity<br/>• Update approval routing"]

        AT["5️⃣ AuditTrailAgent<br/>─────────────<br/>• Write immutable audit record<br/>• Link evidence chain<br/>• Store rollback plan status<br/>• Archive fix artifacts"]

        FV --> MC --> CE --> TU --> AT
    end

    AT --> OUTPUT["📤 feedback_result.json"]
    OUTPUT --> CANARY

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

## 4. Sequence Diagram — Canary Orchestrated Release Flow

The following diagram illustrates the complete execution trace, showing how the outer Canary Controller manages traffic tiers and triggers the internal Feedback Agent sub-agents at each step.

```mermaid
sequenceDiagram
    participant CLI as run_canary.py
    participant CC as CanaryReleaseController
    participant TR as traffic_router.py
    participant FA as FeedbackAgent (main.py)
    participant RB as rollback.py
    participant OCS as OCS Component APIs
    participant DB as Database (PostgreSQL/SQLite)

    CLI->>CC: Initialize(input.json, output_dir)
    CC->>DB: Insert canary record (status='IN_PROGRESS')
    
    loop For each tier (5%, 25%, 50%, 100%)
        CC->>TR: set_traffic_weight(tier_percent, query)
        TR->>OCS: PUT /config-service/v1/traffic-routing (weight payload)
        OCS-->>TR: Response (200 OK)
        Note over CC: Soak (CANARY_SOAK_TIME_SECONDS)
        CC->>FA: run_feedback_pipeline(input.json, feedback_tier_X.json)
        
        Note over FA: Executes 5 sub-agents sequentially:
        FA->>OCS: Verification checks (VerificationAgent)
        FA->>OCS: Latency/Relevance checks (MetricComparisonAgent)
        FA->>FA: s2n & guardrail check (CanaryEvaluationAgent)
        FA->>DB: Update watchlist & runbook templates (ThresholdUpdateAgent)
        FA->>DB: Insert immutable audit log (AuditTrailAgent)
        FA-->>CC: Return feedback_result.json (action=PROMOTE|ROLLBACK|HOLD)
        
        alt decision.action == 'PROMOTE'
            CC->>DB: Update current_tier & tiers_completed in DB
            Note over CC: Continue to next tier
        else decision.action == 'ROLLBACK'
            CC->>RB: execute_rollback(query, incident_id, db, reason)
            RB->>TR: reset_traffic_to_baseline(query)
            TR->>OCS: PUT weight = 0%
            RB->>OCS: POST /config-service/v1/revert
            RB->>DB: UPDATE canary_releases (status='ROLLED_BACK')
            RB->>DB: UPDATE watchlist (status='REGRESSED')
            Note over CC: Break out of rollout loop
        else decision.action == 'HOLD'
            alt hold_count >= max_holds
                CC->>DB: UPDATE canary_releases (status='HELD')
            else
                CC->>DB: UPDATE canary_releases (status='HELD') (Pause progression)
            end
            Note over CC: Break out of rollout loop
        end
    end
    CC->>DB: UPDATE canary_releases (status=final_status)
    CC->>CLI: Return final canary status summary
```

---

## 5. State Machine Lifecycles

### 5.1 Canary Release Orchestrator State Machine

The **CanaryReleaseController** drives progressive weight advancement. It transitions between states based on feedback decisions at each evaluation tier.

```mermaid
stateDiagram-v2
    [*] --> PENDING: Canary release created

    PENDING --> IN_PROGRESS: Initialize tier 5%
    
    state IN_PROGRESS {
        [*] --> SetWeight: set_traffic_weight()
        SetWeight --> SoakTelemetry: Wait for telemetry soak
        SoakTelemetry --> RunFeedback: Execute run_feedback_pipeline()
        RunFeedback --> EvaluateResult: Read decision.action
    }

    EvaluateResult --> PROMOTE: action == PROMOTE
    EvaluateResult --> ROLLBACK: action == ROLLBACK
    EvaluateResult --> HOLD: action == HOLD

    PROMOTE --> IN_PROGRESS: Advance tier (25%, 50%, 100%)
    PROMOTE --> COMPLETED: tier == 100% completed
    
    HOLD --> IN_PROGRESS: hold_count < max_holds (retry same tier)
    HOLD --> HELD: hold_count >= max_holds (Escalate)

    ROLLBACK --> ROLLED_BACK: execute_rollback()

    ROLLED_BACK --> [*]: Traffic reset to 0%
    HELD --> [*]: Operator investigation required
    COMPLETED --> [*]: Rollout finalized at 100%
```

### 5.2 Feedback Loop Pipeline State Machine

Within the `RunFeedback` state, the Feedback Agent executes its five sequential sub-agents to compute verification and metric states.

```mermaid
stateDiagram-v2
    [*] --> Verifying: Start verification checks
    Verifying --> VerificationFailed: Any check fails
    Verifying --> Verified: All 5 checks pass

    VerificationFailed --> RolledBackDecision: Immediate rollback recommended

    Verified --> Measuring: Collect live metrics
    Measuring --> Measured: Deltas & overlap relevance computed

    Measured --> Deciding: Apply guardrails (S2N & Latency)

    Deciding --> PromotedDecision: Metrics positive + S2N >= 5.0
    Deciding --> RolledBackDecision: Latency degraded or S2N < 2.0
    Deciding --> HeldDecision: Inconclusive / 2.0 <= S2N < 5.0

    PromotedDecision --> Learning: Update thresholds & resolve query
    RolledBackDecision --> Learning: Record failure pattern & regress query
    HeldDecision --> Learning: Extend monitoring window

    Learning --> Auditing: Write audit record to DB
    Auditing --> Closed: Pipeline complete
    Closed --> [*]
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

## 8. Output Schemas

### 8.1 Feedback Result Schema — `feedback_result.json`

Produced by the **Feedback Agent pipeline** at each evaluation tier:

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

### 8.2 Canary Release Result Schema — `canary_release_result.json`

Produced by the **CanaryReleaseController** summarizing the complete lifecycle of the progressive rollout:

```json
{
  "agent": "CanaryReleaseController",
  "incident_id": "INC-20260603-001",
  "query": "hybrid work backpack",
  "status": "COMPLETED",
  "tiers_evaluated": 4,
  "tiers_promoted": 4,
  "tier_results": [
    {
      "tier_percent": 5,
      "decision": "PROMOTE",
      "confidence": 0.577,
      "reason": "All verification checks passed...",
      "metrics": {
        "zeroResultRate": {"before": 1.0, "after": 0.0, "delta": -1.0},
        "ctr": {"before": 0.0, "after": "pending_canary", "delta": "n/a"},
        "latency_p95_ms": {"before": 45.0, "after": 52.0, "delta": 7.0},
        "relevanceScore": {"before": 0.0, "after": 0.82, "delta": 0.82}
      },
      "timestamp": "2026-06-05T12:00:00+05:30"
    }
  ],
  "final_traffic_percent": 100,
  "timestamp": "2026-06-05T12:15:05+05:30"
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
