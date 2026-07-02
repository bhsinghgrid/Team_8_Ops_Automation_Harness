# 9. System & Database Architecture Blueprint

This diagram provides a high-fidelity mapping of all project components, backend microservices, orchestration engines, and database systems (including LanceDB and relational database backends).

```mermaid
graph TB
    %% Styling configurations
    classDef frontend fill:#eff6ff,stroke:#1d4ed8,color:#1e3a8a,stroke-width:1.5px;
    classDef backend fill:#f0fdf4,stroke:#15803d,color:#14532d,stroke-width:1.5px;
    classDef db fill:#fff7ed,stroke:#c2410c,color:#7c2d12,stroke-width:2px;
    classDef orchestrator fill:#faf5ff,stroke:#6b21a8,color:#4a154b,stroke-width:1.5px;
    classDef external fill:#f9fafb,stroke:#4b5563,color:#1f2937,stroke-dasharray: 4 2;

    %% Component declarations
    subgraph UI_Layer ["💻 1. Frontend layer (React & Vite)"]
        ReactApp["Vite Dashboard App<br/>(localhost:5173)"]:::frontend
    end

    subgraph API_and_Tracking_Layer ["⚡ 2. Backend & Experiment Services"]
        FastAPI["FastAPI App Server<br/>(localhost:8000)"]:::backend
        MLflow["MLflow Server<br/>(localhost:5000)"]:::backend
    end

    subgraph Orchestration_Layer ["🚦 3. Temporal Workflow Engine"]
        Temporal["Temporal Server<br/>(localhost:7233)"]:::orchestrator
        Worker["Temporal Worker Daemon<br/>(search-ai-task-queue)"]:::orchestrator
    end

    subgraph Autonomous_Agent_Layer ["🧠 4. Sandboxed Agent REPL (fast-rlm)"]
        BaseAgent["BaseAgent Base Class<br/>(base_agent.py)"]:::orchestrator
        DenoHost["Deno Subprocess<br/>(Sandboxed subagents.ts)"]:::orchestrator
        Pyodide["Pyodide REPL VM<br/>(WASM Python Sandbox)"]:::orchestrator
    end

    subgraph Database_Storage_Layer ["🗄️ 5. Database Storage Layer"]
        LanceDB[(LanceDB Vector DB<br/>product_vectors Table)]:::db
        CatalogDB[(Catalog Relational DB<br/>mock_catalog_db.db)]:::db
        RulesDB[(Search Rules DB<br/>mock_search_rules_db.json)]:::db
        VectorStore[(mock_vector_db.json)]:::db
    end

    subgraph LLM_Cloud_Layer ["☁️ 6. Foundation Model APIs"]
        VertexAI["Google Vertex AI<br/>(Gemini 2.5 on Endpoints)"]:::external
        AIStudio["Google AI Studio<br/>(Gemini Flash/Pro via Keys)"]:::external
    end

    %% Wiring and data-flow interactions
    ReactApp <-->|REST API Calls<br/>Port 8000| FastAPI
    ReactApp -.->|Visualizes Runs<br/>Port 5000| MLflow

    FastAPI -->|1. Ingests Logging Signals| CatalogDB
    FastAPI -->|2. Triggers Repair Workflows| Temporal
    Temporal <-->|Runs Pipeline| Worker

    %% Worker activities routing
    Worker -->|RCA Activity| BaseAgent
    BaseAgent -->|A. Spawns| DenoHost
    DenoHost -->|B. Initializes| Pyodide
    Pyodide <-->|C. Queries/Resolves Tools| BaseAgent
    
    %% Repository connections to Databases
    BaseAgent <-->|Reads Products| CatalogDB
    BaseAgent <-->|Reads/Writes Rules| RulesDB
    BaseAgent <-->|Vector Synced Mapping| VectorStore
    BaseAgent <-->|Distance Calculations| LanceDB

    %% External LLM integrations
    Pyodide -->|HTTPS Prompt Checks| VertexAI
    Pyodide -->|HTTPS Prompt Checks| AIStudio

    %% Activity logging connections
    Worker -->|Logs Run Spans| MLflow
    BaseAgent -->|Logs Diagnostic Steps| MLflow

    %% Layout hints
    style Database_Storage_Layer fill:#fffbf7,stroke:#ffedd5,stroke-width:2px;
    style Autonomous_Agent_Layer fill:#fafaff,stroke:#f3e8ff,stroke-width:2px;
```
