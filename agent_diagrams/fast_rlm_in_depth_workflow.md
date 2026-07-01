# In-Depth FAST-RLM Workflow

This diagram illustrates the in-depth workings of the FAST-RLM engine, including the "Reason-Act" loop and the process of spawning a recursive sub-agent with its own sandboxed REPL environment.

```mermaid
graph TD
    subgraph "Main Agent Execution"
        direction TB
        A[Start: Agent Receives Goal + Data] --> B{FAST-RLM Engine};
        B --> C["LLM Reasons: 'What should I do next?'"];
        C --> D{"Decides to Call a Tool"};
        D -- Standard Tool --> E[Tool is Executed<br/>e.g., catalog_coverage()];
        E --> F[Result is Returned];
        F --> B;
        D -- Final Answer --> G[Agent Returns Final JSON Output];
    end

    subgraph "Recursive Sub-Agent for Deep Investigation"
        direction TB
        D -- Calls 'run_deep_rca_investigation' --> H{New FAST-RLM Instance};
        H --> I["Sub-Agent LLM Reasons<br/>(e.g., 'How can I analyze this data?')"];
        I --> J{"Decides to Write Python Code"};
        J --> K["Sandboxed REPL<br/>(Code is executed safely)"];
        K --> L[Code Output is Returned];
        L --> H;
        J -- Sub-Problem Solved --> M[Sub-Agent Returns Result];
        M -- Result Becomes 'Observation' --> F
    end

    style B fill:#eef8f0,stroke:#14532d
    style H fill:#fffbeb,stroke:#f59e0b
```
