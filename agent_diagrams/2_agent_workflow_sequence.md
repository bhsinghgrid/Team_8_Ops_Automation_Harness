sequenceDiagram
    participant User
    participant WorkflowTrigger as run_unified_workflow.py
    participant Temporal
    participant RootCauseAgent
    participant FixProposalAgent
    participant DiffyServer
    participant EvalAgent
    participant MLflow
    participant ReleaseAgent
    participant FeedbackAgent

    %% 1. Start Workflow
    User->>WorkflowTrigger: Run workflow (signal type: "catalog")
    WorkflowTrigger->>Temporal: Start Workflow(signal)

    %% 2. Root Cause Analysis
    Temporal->>RootCauseAgent: Execute RCA
    RootCauseAgent-->>Temporal: Return RCA results

    %% 3. Generate Fix Proposal
    Temporal->>FixProposalAgent: Generate Fix Plan(RCA results)
    FixProposalAgent->>DiffyServer: Create Shadow Test
    DiffyServer-->>FixProposalAgent: Return diff_id
    FixProposalAgent-->>Temporal: Return Fix Plan + diff_id

    %% 4. Evaluate Fix
    Temporal->>EvalAgent: Evaluate Fix(diff_id)
    EvalAgent->>DiffyServer: Fetch Shadow Test Report
    DiffyServer-->>EvalAgent: Return Evaluation Report
    EvalAgent->>MLflow: Log Metrics & Artifacts
    EvalAgent-->>Temporal: Return Evaluation Decision

    %% 5. Release Decision
    Temporal->>ReleaseAgent: Execute Release
    ReleaseAgent-->>Temporal: Return Release Status

    %% 6. Feedback Loop
    Temporal->>FeedbackAgent: Generate Final Feedback
    FeedbackAgent-->>Temporal: Return Workflow Summary

    %% 7. Workflow Completion
    Temporal-->>WorkflowTrigger: Workflow Completed
    WorkflowTrigger-->>User: Display Results