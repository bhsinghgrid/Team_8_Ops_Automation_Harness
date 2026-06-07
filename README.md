# Runbook System Final

This repository contains the final version of the Runbook System, an automated pipeline that leverages AI agents to analyze operational signals, diagnose root causes, assess business impact, identify data gaps, evaluate potential fixes, and generate comprehensive runbooks.

## Project Structure

The core logic of the system is organized as follows:

-   `agents/`: Contains the individual AI agents that perform specific tasks within the pipeline.
    -   `root_cause/`: Logic for diagnosing the root cause of an operational signal.
    -   `impact/`: Logic for assessing the business impact of the identified root cause.
    -   `data_gap/`: Logic for identifying missing data quality tests and monitoring gaps.
    -   `eval/`: Logic for evaluating potential fixes through shadow testing.
    -   `fix_plan/`: Logic for synthesizing the final fix plan and governance.
-   `orchestration/`: Manages the overall pipeline flow and interactions between components.
    -   `orchestrator.py`: The main script that coordinates the execution of all agents.
    -   `rlm_client.py`: Client for interacting with the Reasoning and Language Model (RLM).
    -   `database.py`: Handles persistent storage of runbooks (using SQLite for local ease).
    -   `config.py`: Configuration settings for the orchestration layer.
-   `shared/`: Defines common data structures and schemas used across the system.
    -   `schemas.py`: Pydantic models for `OpsSignal`, `Runbook`, `RootCauseReport`, etc.
-   `tools/`: Provides utility functions and helper modules for various agents.
    -   `approval_tools.py`: Logic for determining human approval requirements.
    -   `owner_tools.py`: Maps capabilities to their respective owners.
    -   (Other tool files for various specific functionalities)
-   `samples/`: Example input JSON files for testing the pipeline locally.
-   `Magellan-signal-ingestion-backend/`: (Assumed external dependency for mock data, specifically `mock-data/scenarios/catalog_scenarios.json` for pipeline input)

## Setup and Installation

### Prerequisites

*   Python 3.9+
*   pip (Python package installer)
*   (Optional but Recommended) A virtual environment tool like `venv` or `conda`.
*   A Google Gemini API Key with sufficient authentication scopes, set as `GEMINI_API_KEY` in a `.env` file at the project root.

### Steps

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd Runbook_System_Final
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate # On Windows, use `.venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Gemini API Key:**
    Create a `.env` file in the root of the `/Users/bhsingh/Documents/Capstone_Final/Agents` directory (where `Runbook_System_Final` resides) with your Google Gemini API key:
    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```
    Replace `"YOUR_GEMINI_API_KEY"` with your actual key.

## Running the Pipeline

The pipeline can be executed using the `run_pipeline.py` script. By default, it uses a sample input from the `Magellan-signal-ingestion-backend/mock-data/scenarios/catalog_scenarios.json`.

```bash
python run_pipeline.py
```

### Example Output

(Output will vary based on RLM responses and Diffy Proxy status, but will follow a similar structure to the console output seen during development)

## Dockerization

To run this project within a Docker container, follow these steps:

### Build the Docker image

```bash
docker build -t runbook-system .
```

### Run the Docker container

```bash
docker run -e GEMINI_API_KEY="YOUR_GEMINI_API_KEY" runbook-system
```

Replace `"YOUR_GEMINI_API_KEY"` with your actual Google Gemini API Key.

**Note on Diffy Proxy**: The Eval Factory agent attempts to connect to a Diffy Proxy at `http://localhost:31900/search`. If you are running this in Docker, `localhost` will refer to the container's localhost, not your host machine's. You may need to configure Docker networking or run Diffy within the same Docker network for this part of the pipeline to function correctly.

## Integration with Existing Systems

This pipeline is designed to be integrated into existing operational systems or incident management workflows. The primary entry point for programmatic interaction is the `execute_pipeline` function located in `orchestration/orchestrator.py`.

### `execute_pipeline` Function

```python
async def execute_pipeline(signal_data: dict) -> Runbook:
    """
    Runs the full agent pipeline from a raw signal to a final runbook.
    """
```

**Parameters:**

*   `signal_data` (dict): A dictionary representing the operational signal. This dictionary should conform to the structure expected by the `OpsSignal` Pydantic schema (defined in `shared/schemas.py`). An example structure is shown in `Magellan-signal-ingestion-backend/mock-data/scenarios/catalog_scenarios.json`.

**Returns:**

*   `Runbook`: A Pydantic `Runbook` object (defined in `shared/schemas.py`) containing the complete analysis, including root cause, impact, prevention plan, evaluation report, and the final fix plan.

### Example Integration

To integrate, you would typically:

1.  **Import `execute_pipeline`**:
    ```python
    from Runbook_System_Final.orchestration.orchestrator import execute_pipeline
    from Runbook_System_Final.shared.schemas import OpsSignal, Runbook # For type hinting and understanding structure
    ```
2.  **Prepare `signal_data`**: Construct a dictionary matching the `OpsSignal` schema. This data would usually come from your monitoring or alerting systems.
    ```python
    my_signal_data = {
        "signals": [
            {
                "id": "your-system-alert-id",
                "type": "your_signal_type",
                "source": "your_monitoring_system",
                "severity": "high",
                "summary": "Brief description of the incident",
                "detectedAt": "2026-06-07T12:00:00Z",
                "entities": {
                    "key": "value"
                },
                "metrics": {
                    "key": 123
                },
                "evidence": [
                    {
                        "field": "field_name",
                        "value": "field_value",
                        "message": "Evidence message"
                    }
                ],
                "recommendedAction": "Action from your system (if any)"
            }
        ]
    }
    ```
3.  **Call `execute_pipeline`**:
    ```python
    import asyncio

    async def run_integration():
        final_runbook = await execute_pipeline(my_signal_data)
        print(f"Generated Runbook ID: {final_runbook.runbook_id}")
        print(f"Approval Required: {final_runbook.approval_required}")
        print("Fix Plan:")
        for step in final_runbook.immediate_fix_plan:
            print(f"- {step}")

    if __name__ == "__main__":
        asyncio.run(run_integration())
    ```

### Considerations for Production Deployment

*   **API Key Management**: Securely manage your `GEMINI_API_KEY` (e.g., using environment variables, Kubernetes secrets, or a secrets management service).
*   **Diffy Proxy**: Ensure the Diffy Proxy (or its equivalent in your system) is accessible to the pipeline for shadow testing if that functionality is critical.
*   **Error Handling**: Implement robust error handling around the `execute_pipeline` call to manage RLM failures, connection issues, and other potential problems.
*   **Scalability**: Consider how to scale the pipeline if you anticipate a high volume of signals.
*   **Custom Agents/Tools**: The modular structure allows for extending the pipeline with custom agents or integrating additional specialized tools.
