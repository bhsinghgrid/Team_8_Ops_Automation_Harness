# Autocomplete Agent and FAST-RLM Workflow

This diagram illustrates how the Autocomplete agents use FAST-RLM to identify and fix issues related to search suggestions, using specialized tools for typo tolerance, prefix matching, and popularity bias.

```mermaid
graph TD
    subgraph "User Input"
        Signal["Autocomplete Signal<br/>(e.g., 'no results for shos')"]
    end

    subgraph "FAST-RLM Execution Engine"
        FastRLM["FAST-RLM Engine"]
    end

    subgraph "Autocomplete Agents (Inherit from BaseAgent)"
        RCA_Autocomplete["AutocompleteRootCauseAgent"]
        Fix_Autocomplete["AutocompleteFixProposalAgent"]
    end

    subgraph "Standard Tools (for known issues)"
        direction LR
        T1["run_typo_tolerance_analysis"]
        T2["run_prefix_matching_analysis"]
        T3["update_typo_dictionary"]
    end

    subgraph "Dynamic Sub-Agent (for unknown issues)"
        DeepRCA["run_deep_rca_investigation"]
        SubAgent["Specialist Sub-Agent<br/>(Writes & Executes Python)"]
        DeepRCA --> SubAgent
    end

    Signal --> RCA_Autocomplete
    RCA_Autocomplete -- uses --> FastRLM
    FastRLM -- calls --> T1
    FastRLM -- calls --> T2
    
    RCA_Autocomplete -- sends RCA to --> Fix_Autocomplete
    Fix_Autocomplete -- uses --> FastRLM
    FastRLM -- calls --> T3
    FastRLM -- can also call --> DeepRCA

    style FastRLM fill:#eef8f0,stroke:#14532d
    style DeepRCA fill:#fff7ed,stroke:#f59e0b
    style SubAgent fill:#fffbeb,stroke:#f59e0b
```
