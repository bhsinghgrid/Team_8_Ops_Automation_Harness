
    User([User])

    subgraph "User Interfaces"
        UI_Frontend["Frontend UI<br/>(localhost:5173)"]
        UI_Diffy["Diffy UI<br/>(localhost:8880)"]
        UI_MLflow["MLflow UI<br/>(localhost:5001)"]
        UI_Temporal["Temporal UI<br/>(localhost:8233)"]
    end

    subgraph "Backend Services (Docker)"
        Service_Backend["FastAPI Backend<br/>(localhost:8000)"]
        Service_Diffy["Diffy Server"]
        Service_Mongo["MongoDB"]
        Service_Redis["Redis"]
    end

    subgraph "Workflow Orchestration"
        Service_Temporal["Temporal Server"]
        Service_Worker["Temporal Worker<br/>(Runs AI Agents)"]
        Service_MLflow["MLflow Server"]
    end

    subgraph "External Services"
        Service_GoogleAI["Google AI Platform<br/>(Gemini API)"]
    end

    %% User Access
    User --> UI_Frontend
    User --> UI_Diffy
    User --> UI_MLflow
    User --> UI_Temporal

    %% Application Flow
    UI_Frontend --> Service_Backend
    Service_Backend --> Service_Temporal
    Service_Temporal --> Service_Worker

    %% Worker Integrations
    Service_Worker --> Service_GoogleAI
    Service_Worker --> Service_Diffy
    Service_Worker --> Service_MLflow

    %% Diffy Dependencies
    Service_Diffy --> Service_Mongo
    Service_Diffy --> Service_Redis