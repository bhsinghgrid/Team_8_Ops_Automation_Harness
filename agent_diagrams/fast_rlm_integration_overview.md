# FAST-RLM Integration Overview

This diagram illustrates how your agents are integrated with the FAST-RLM engine, showing the relationship between the `BaseAgent`, the FAST-RLM engine, and the dynamically spawned sub-agents for deep analysis.

```mermaid
graph TD
    subgraph "Your Agent Implementations"
        direction LR
        Catalog["CatalogRootCauseAgent"]
        Autocomplete["AutocompleteRootCauseAgent"]
        Semantic["SemanticRootCauseAgent"]
    end

    subgraph "Core Architecture"
        BaseAgent["BaseAgent (base_agent.py)<br/>- Configures fast_rlm<br/>- Registers Tools"]
        FastRLM["FAST-RLM Engine<br/>(fast_rlm.run)"]
        BaseAgent --> FastRLM
    end

    subgraph "Standard Toolset (Pre-defined)"
        direction TB
        CatalogTools["catalog_coverage<br/>search_quality<br/>..."]
        AutocompleteTools["run_prefix_matching<br/>run_typo_tolerance<br/>..."]
        SemanticTools["embedding_drift<br/>vector_db_health<br/>..."]
    end

    subgraph "Dynamic Sub-Agent for Deep Analysis"
        direction TB
        DeepRCA["run_deep_rca_investigation<br/>(Tool in BaseAgent)"]
        SubAgent["Specialist Sub-Agent<br/>(Spawned by FAST-RLM)"]
        Repl["Sandboxed REPL Environment<br/>- Writes/Executes Python<br/>- Analyzes raw data"]
        DeepRCA --> SubAgent --> Repl
    end

    Catalog -- Inherits --> BaseAgent
    Autocomplete -- Inherits --> BaseAgent
    Semantic -- Inherits --> BaseAgent

    FastRLM -- Executes --> CatalogTools
    FastRLM -- Executes --> AutocompleteTools
    FastRLM -- Executes --> SemanticTools
    FastRLM -- Executes --> DeepRCA

    style BaseAgent fill:#eef8f0,stroke:#14532d
    style Catalog fill:#f0f9ff,stroke:#0284c7
    style Autocomplete fill:#f0f9ff,stroke:#0284c7
    style Semantic fill:#f0f9ff,stroke:#0284c7
    style DeepRCA fill:#fff7ed,stroke:#f59e0b
    style SubAgent fill:#fffbeb,stroke:#f59e0b
    style Repl fill:#fffbeb,stroke:#f59e0b
```
