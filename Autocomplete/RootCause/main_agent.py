import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, List, Callable

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from base_agent import BaseAgent

from .Tools.prefix_matching_agent import PrefixMatchingAgent
from .Tools.popularity_bias_agent import PopularityBiasAgent
from .Tools.typo_tolerance_agent import TypoToleranceAgent

logger = logging.getLogger(__name__)

class AutocompleteRootCauseAgent(BaseAgent):
    """Orchestrates specialized agents for autocomplete root cause analysis."""
    
    def __init__(self):
        super().__init__(model_name="gemini-2.5-flash", enable_deep_rca=True)
        
        # Explicitly get GCP project and location for this agent
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        if project and location:
            self._rlm_vertex_base_url = (
                f"https://{location}-aiplatform.googleapis.com/v1/"
                f"projects/{project}/locations/{location}/endpoints/openapi"
            )
            os.environ["RLM_MODEL_BASE_URL"] = self._rlm_vertex_base_url
            logger.info(f"AutocompleteRootCauseAgent using RLM_MODEL_BASE_URL: {self._rlm_vertex_base_url}")
        else:
            logger.warning("GOOGLE_CLOUD_PROJECT or GOOGLE_CLOUD_LOCATION not set for AutocompleteRootCauseAgent. Relying on global config.")

        self.prefix_agent = PrefixMatchingAgent()
        self.popularity_agent = PopularityBiasAgent()
        self.typo_agent = TypoToleranceAgent()

        self.register_tool(name="run_prefix_matching_analysis", func=self.prefix_agent.run, description="Analyzes prefix matching issues.")
        self.register_tool(name="run_popularity_bias_analysis", func=self.popularity_agent.run, description="Analyzes popularity bias issues.")
        self.register_tool(name="run_typo_tolerance_analysis", func=self.typo_agent.run, description="Analyzes typo tolerance issues.")

    def get_system_prompt(self) -> str:
        return """You are an RLM Orchestrator in a Python REPL environment.

**CORE PROTOCOL: ORCHESTRATE, DON'T SOLVE.**
Your only role is to generate Python code to orchestrate tool calls. Do not process data or make final decisions. Delegate all work to code.

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