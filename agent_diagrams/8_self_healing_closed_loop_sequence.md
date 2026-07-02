# 8. Self-Healing Closed-Loop Sequence Diagram

This diagram shows the complete end-to-end telemetry-driven repair sequence managed by the **Temporal Orchestration Engine**, showing how an issue is detected, diagnosed, patched, and dynamically evaluated.

```mermaid
sequenceDiagram
    autonumber
    actor User as Client Traffic / Log stream
    participant AG as API Gateway & Logs
    participant WH as Temporal Orchestrator
    participant RCA as Root Cause Agent (RCA)
    participant FIX as Fix Proposal Agent
    participant EV as Evaluation Agent (Shadow Test)
    participant CR as Canary Release Agent
    participant FB as Feedback Post-Release Auditor

    User->>AG: Triggers queries (clicks / cart additions)
    AG->>AG: Log anomalies flagged (e.g., 404 SKUs, embedding drift)
    AG->>WH: Publish anomaly event batch (signal)
    
    rect rgb(240, 248, 255)
        note right of WH: Phase 1: Automated Diagnosis
        WH->>RCA: Invoke RCA Agent with context & events list
        RCA->>RCA: Parse events inside WASM Pyodide sandbox
        RCA-->>WH: Return structured JSON Root Cause Finding
    end

    rect rgb(255, 245, 238)
        note right of WH: Phase 2: Autonomous Patching
        WH->>FIX: Invoke Fix Agent with identified root cause
        FIX->>FIX: Select correct remediations (e.g. index rebuild, cache invalidation)
        FIX-->>WH: Return executable Fix Action Patch
    end

    rect rgb(245, 255, 250)
        note right of WH: Phase 3: Traffic-Mirroring Shadow Evaluation
        WH->>EV: Invoke Evaluation Agent with baseline logs & candidates
        EV->>EV: Extract dynamic click clickstream ground-truth
        EV->>EV: Calculate IR Metrics (MRR, Recall, NDCG@10) using ranx
        EV-->>WH: Return Comparison Metrics report (Decision: PROMOTE_TO_CANARY)
    end

    rect rgb(254, 244, 254)
        note right of WH: Phase 4 & 5: Gated Release & Verification
        WH->>WH: Check Gating Rule (Threshold: NDCG >= 0.84)
        WH->>CR: Trigger Canary Deployment to 10% traffic container
        CR->>AG: Deploy candidates & monitor runtime telemetry
        CR-->>WH: Deployment Status Confirmation (Success)
        WH->>FB: Invoke Feedback Supervisor Agent
        FB->>FB: Audit post-deployment telemetry & errors
        FB-->>WH: Approve Promotion to 100% Production
    end
```
