# Semantic Agent and FAST-RLM Workflow

This diagram shows how the Semantic agents use FAST-RLM to investigate complex issues related to vector embeddings and semantic search relevance, with the ability to use a deep investigation sub-agent for direct data analysis.

```mermaid
graph TD
    subgraph "User Input"
        Signal["Semantic Signal<br/>(e.g., 'low relevance for similar queries')"]
    end

    subgraph "FAST-RLM Execution Engine"
        FastRLM["FAST-RLM Engine"]
    end

    subgraph "Semantic Agents (Inherit from BaseAgent)"
        RCA_Semantic["SemanticRootCauseAgent"]
        Fix_Semantic["SemanticFixProposalAgent"]
    end

    subgraph "Standard Tools (for known issues)"
        direction LR
        T1["embedding_drift"]
        T2["vector_db_health"]
        T3["vector_refresh"]
        T4["semantic_reindex_trigger"]
    end

    subgraph "Dynamic Sub-Agent (for unknown issues)"
        DeepRCA["run_deep_rca_investigation"]
        SubAgent["Specialist Sub-Agent<br/>(Writes & Executes Python)"]
        DeepRCA --> SubAgent
    end

    Signal --> RCA_Semantic
    RCA_Semantic -- uses --> FastRLM
    FastRLM -- calls --> T1
    FastRLM -- calls --> T2
    
    RCA_Semantic -- sends RCA to --> Fix_Semantic
    Fix_Semantic -- uses --> FastRLM
    FastRLM -- calls --> T3
    FastRLM -- calls --> T4
    FastRLM -- can also call --> DeepRCA

    style FastRLM fill:#eef8f0,stroke:#14532d
    style DeepRCA fill:#fff7ed,stroke:#f59e0b
    style SubAgent fill:#fffbeb,stroke:#f59e0b
```
