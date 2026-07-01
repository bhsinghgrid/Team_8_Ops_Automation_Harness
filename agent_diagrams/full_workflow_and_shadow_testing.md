```mermaid
graph TD
    subgraph Overall Unified Search AI Repair Workflow
        subgraph Initialization
            A[Start: User runs run_unified_workflow.py] --> B(UnifiedSearchAiRepairWorkflow);
        end

        subgraph "Phase 1: Specialized Root Cause & Fix"
            B --> C{Inspects Signal Type};
            C -->|"type: catalog"| D[catalog_root_cause_activity];
            D --> E[catalog_fix_proposal_activity];

            C -->|"type: autocomplete"| F[autocomplete_root_cause_activity];
            F --> G[autocomplete_fix_proposal_activity];

            C -->|"type: semantic"| H[semantic_root_cause_activity];
            H --> I[semantic_fix_proposal_activity];
        end

        subgraph "Phase 2: Shared Evaluation & Release"
            E --> J[Shared eval_activity];
            G --> J;
            I --> J;

            J --> K{Check Metrics: NDCG < 0.84?};
            K -->|Yes| L[Workflow Pauses for Approval];
            L --> M[User runs signal_workflow.py];
            M --> N[Shared release_activity];

            K -->|No| N;
            N --> O[End: Workflow Complete];
        end
    end

    subgraph "Detailed Shadow Testing Agent Diagram (Shared Eval Activity)"
        subgraph Primary User Flow (Production)
            P[Production Request] --> Q(ShadowTestEngine);
            Q -->|1. Call Champion Model| R(ModelClient);
            R --> S[Champion Response];
            S --> T[Return to User];
            S --> U[Champion Response for Eval];
        end

        Q -->|2. Mirror Request?| V{TrafficMirror};
        V -->|Yes| W(ModelClient);
        W -->|3. Call Challenger Model| X[Challenger Response];

        subgraph "4. Evaluation & Analysis"
            U --> Y(Evaluator);
            X --> Y;
            Y --> Z1[MLflow Tracer];
            Y --> Z2[Redis Storage];
            Y --> Z3(Gating Engine);
        end

        subgraph "Observability & Automation"
            Z2 -->|5. Read for Summary| AA[Monitoring Dashboard];
            Z3 -->|6. Trigger Alert| AA;
            Z3 -->|7. Trigger Promotion| BB[Deployment Agent];
        end
    end

    style J fill:#f9f,stroke:#333,stroke-width:2px;
```
