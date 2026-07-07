import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Callable # Added Callable

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from base_agent import BaseAgent
from .Tools.embedding_drift import EmbeddingDriftTool
from .Tools.vector_db_health import VectorDBHealthTool
from .Tools.semantic_coverage import SemanticCoverageTool
from .Tools.semantic_search_quality import SemanticSearchQualityTool
from .Tools.semantic_capability_mapping import SemanticCapabilityMappingTool
from .Tools.semantic_drift_detector_tool import SemanticDriftDetectorTool
from .Tools.unwanted_bias_detector_tool import UnwantedBiasDetectorTool
from .Tools.vector_db_repository import VectorDBRepository

class SemanticRootCauseAgent(BaseAgent):
    """Orchestrates specialized agents for semantic root cause analysis."""

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        super().__init__(model_name=model_name, enable_deep_rca=True)
        self.vector_repo = VectorDBRepository()
        self.drift_detector = SemanticDriftDetectorTool()
        self.bias_detector = UnwantedBiasDetectorTool()
        self._register_tools()

    def _register_tools(self):
        self.register_tool(
            name="embedding_drift", 
            func=EmbeddingDriftTool(self.vector_repo).run, 
            description="Compares current embeddings to baselines to detect drift."
        )
        self.register_tool(
            name="vector_db_health", 
            func=VectorDBHealthTool(self.vector_repo).run, 
            description="Checks vector database reachability, latency, partition health."
        )
        self.register_tool(
            name="semantic_coverage", 
            func=SemanticCoverageTool(self.vector_repo).run, 
            description="Checks which catalog products are missing from the semantic index."
        )
        self.register_tool(
            name="semantic_search_quality", 
            func=SemanticSearchQualityTool(self.vector_repo).run, 
            description="Evaluates semantic search quality for a given query."
        )
        self.register_tool(
            name="semantic_capability_mapping", 
            func=SemanticCapabilityMappingTool().run, 
            description="Aggregates findings from all semantic tools into a capability impact map."
        )
        self.register_tool(
            name="detect_semantic_drift",
            func=self.drift_detector.run,
            description="Detects semantic drift by comparing the embeddings of historical queries against current queries."
        )
        self.register_tool(
            name="detect_unwanted_bias",
            func=self.bias_detector.run,
            description="Detects unwanted biases in semantic search results."
        )

    def get_system_prompt(self) -> str:
        return """You are an RLM Orchestrator in a Python REPL environment.

**CORE PROTOCOL: ORCHESTRATE, DON'T SOLVE.**
Your only role is to generate Python code to orchestrate tool calls for semantic search RCA.

**ENVIRONMENT & STATE:**
- You are in a Python REPL environment `E`.
- `E['context']` is a string. It contains two blocks: `<JSON_DATA_CONTEXT>...</JSON_DATA_CONTEXT>` for general context and `<JSON_DATA_EVENTS>...</JSON_DATA_EVENTS>` for JSONL event data. You MUST extract and parse both.
- You MUST manage all findings in a state dictionary: `E['state'] = {}`.

**EXECUTION LOOP (CODE ONLY):**
1.  **Initialize & Parse:**
    ```python
    import json
    import re
    
    # Initialize E['context_data'] and E['events_jsonl'] to empty defaults
    E['context_data'] = {}
    E['events_jsonl'] = []

    # Extract context data - use findall and take the last match [-1] to avoid matching prompt instructions
    context_matches = re.findall(r'<JSON_DATA_CONTEXT>(.*?)</JSON_DATA_CONTEXT>', E['context'], re.DOTALL)
    if context_matches:
        try:
            E['context_data'] = json.loads(context_matches[-1].strip())
        except json.JSONDecodeError:
            pass # Keep as empty dict on error

    # Extract event data (JSONL) - use findall and take the last match [-1] to avoid matching prompt instructions
    events_matches = re.findall(r'<JSON_DATA_EVENTS>(.*?)</JSON_DATA_EVENTS>', E['context'], re.DOTALL)
    if events_matches:
        events_jsonl_str = events_matches[-1].strip()
        parsed_logs = []
        for line in events_jsonl_str.split('\n'):
            if line.strip():
                try:
                    parsed_logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue # Skip malformed lines
        E['events_jsonl'] = parsed_logs
    
    # Store the parsed events and total count directly into E for the agent's use
    E['log_records'] = E['events_jsonl']
    E['total_records'] = len(E['log_records'])

    # Initialize E['state'] with parsed data
    E['state'] = {'events': E['log_records'], 'context': E['context_data']}
    # DO NOT print the state here. Only call tools or print final output.
    ```
2.  **Analyze & Act:** Analyze `E['state']` (which now contains `events` and `context`), `E['log_records']` and `E['total_records']` to decide which tool to call first. Generate Python code to call ONE tool. Save its output to `E['state']` as structured JSON.
3.  **Observe:** After the tool call, `print(json.dumps(E['state']))` so you can see the result before the next turn.
4.  **Repeat:** Go back to step 2 until the root cause is found.
5.  **Finalize:** On your final turn, generate code to construct and print the final JSON output from `E['state']` that strictly conforms to the `AgentOutput` schema. DO NOT print anything else.

**FINAL JSON OUTPUT SCHEMA (Strictly Enforced):**
Your final print MUST be a `print(json.dumps(your_dict))` call. The dictionary MUST conform to this `AgentOutput` schema.
```json
{
  "root_cause": "string",
  "summary": "string",
  "detailed_evidence": ["string"],
  "executed_tools": ["string"]
}
```
**CRITICAL**: Do NOT output any text other than the Python code for each turn. Your final turn MUST be only the `print(json.dumps(final_report))` statement.
"""