# Catalog Agent and FAST-RLM Workflow

This diagram shows how the Catalog agents use the FAST-RLM engine to diagnose issues and execute fixes, leveraging both standard tools and the deep investigation sub-agent for complex problems.

```mermaid
graph TD
    subgraph "User Input"
        Signal["Catalog Signal<br/>(e.g., from search_events.jsonl)"]
    end

    subgraph "FAST-RLM Execution Engine"
        FastRLM["FAST-RLM Engine"]
    end

    subgraph "Catalog Agents (Inherit from BaseAgent)"
        RCA_Catalog["CatalogRootCauseAgent"]
        Fix_Catalog["GoogleFixProposalAgent"]
    end

    subgraph "Standard Tools (for known issues)"
        direction LR
        T1["catalog_coverage"]
        T2["search_quality"]
        T3["apply_patch"]
        T4["trigger_reindex"]
    end

    subgraph "Dynamic Sub-Agent (for unknown issues)"
        DeepRCA["run_deep_rca_investigation"]
        SubAgent["Specialist Sub-Agent<br/>(Writes & Executes Python)"]
        DeepRCA --> SubAgent
    end

    Signal --> RCA_Catalog
    RCA_Catalog -- uses --> FastRLM
    FastRLM -- calls --> T1
    FastRLM -- calls --> T2
    
    RCA_Catalog -- sends RCA to --> Fix_Catalog
    Fix_Catalog -- uses --> FastRLM
    FastRLM -- calls --> T3
    FastRLM -- calls --> T4
    FastRLM -- can also call --> DeepRCA

    style FastRLM fill:#eef8f0,stroke:#14532d
    style DeepRCA fill:#fff7ed,stroke:#f59e0b
    style SubAgent fill:#fffbeb,stroke:#f59e0b
```
