import asyncio
import json
import os
from dataclasses import dataclass, asdict, field
from typing import Any, Callable
import logging
# import io
import subprocess
        
from dotenv import load_dotenv
# load_dotenv() is called inside BaseAgent.run_agent() instead of at module level
# to avoid NameError in fast-rlm's Pyodide sandbox execution environment.

import fast_rlm
from fast_rlm import RLMConfig

from base_agent import BaseAgent
from temporal.shared import HeartbeatingStream # Consolidated HeartbeatingStream
from Catalog.RootCause.Tools.common_signals import sample_signal
from Catalog.RootCause.Tools.catalog_coverage_tool import CatalogCoverageTool
from Catalog.RootCause.Tools.schema_validation import CatalogSchemaValidationTool
from Catalog.RootCause.Tools.freshness import CatalogFreshnessTool
from Catalog.RootCause.Tools.historical_intent import CatalogHistoricalIntentTool
from Catalog.RootCause.Tools.search_Quality import CatalogSearchQualityTool
from Catalog.RootCause.Tools.capability_mapping_tools import CatalogCapabilityMappingTool
from Catalog.RootCause.Tools.catalog_repository import CatalogRepository
from Catalog.RootCause.Tools.embedding import CatalogEmbeddingTool
from Catalog.RootCause.Tools.vector_sync import CatalogVectorSyncTool
from Catalog.RootCause.Tools.query_intent import QueryIntentDriftTool
from Catalog.RootCause.Tools.index import SearchIndexCoverageTool
from Catalog.RootCause.Tools.query_intent_repository import QueryIntentRepository
from Catalog.RootCause.Tools.search_index_repository import SearchIndexRepository
# from Catalog.RootCause.Tools.common_signals import sample_signal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# # class HeartbeatingStream(io.StringIO):
# #     def write(self, s):
# #         if s and s.strip():
# #             details = s[:3800]  # Truncate to avoid hitting Temporal heartbeat limits
# #             try:
# #                 activity.heartbeat(details)
# #                 logger.info(f"Heartbeat: {details}")  # Also log to worker console
# #             except RuntimeError:  # Thrown when not in an activity context
# #                 pass
# #         super().write(s)


# =========================
# OUTPUT MODEL
# =========================

@dataclass
class AgentOutput:
    overall_status: str
    root_cause: str
    affected_capabilities: list[str]
    summary: str
    detailed_evidence: list[str]
    executed_tools: list[str] = field(default_factory=list)


# =========================
# ADK AGENT
# =========================


class GoogleRootCauseAgent(BaseAgent):

    def __init__(self, model: str = "gemini-2.5-flash"):
        super().__init__(model_name="gemini-2.5-flash", enable_deep_rca=True)

        self.repo = CatalogRepository()
        self.query_repo = QueryIntentRepository()
        self.search_repo = SearchIndexRepository()

        # -------------------------
        # NATIVE TOOL IMPLEMENTATIONS (all tools)
        # -------------------------
        self.register_tool(
            name="catalog_coverage",
            func=CatalogCoverageTool(self.repo).run,
            description="Analyzes a batch of search events to find zero-result queries, which indicates missing products in the catalog."
        )
        self.register_tool(
            name="search_quality",
            func=CatalogSearchQualityTool(self.repo).run,
            description="Analyzes a batch of search events to evaluate search result quality and relevance, looking for low-scoring results."
        )
        self.register_tool(
            name="schema_validation",
            func=CatalogSchemaValidationTool(self.repo).run,
            description="Validates the schema of catalog data against the expected format."
        )
        self.register_tool(
            name="freshness",
            func=CatalogFreshnessTool(self.repo).run,
            description="Checks how recently the catalog data has been updated."
        )
        self.register_tool(
            name="historical_intent",
            func=CatalogHistoricalIntentTool(self.query_repo).run,
            description="Analyzes historical query data to identify trends or changes in user search behavior."
        )
        self.register_tool(
            name="embedding",
            func=CatalogEmbeddingTool(self.repo).run,
            description="Analyzes the vector embeddings of products to find inconsistencies."
        )
        self.register_tool(
            name="vector_sync",
            func=CatalogVectorSyncTool(self.repo).run,
            description="Checks if the vector embeddings are synchronized with the latest product data."
        )
        self.register_tool(
            name="query_intent_drift",
            func=QueryIntentDriftTool(self.query_repo).run,
            description="Detects any significant changes or 'drift' in the intent behind user queries over time."
        )
        self.register_tool(
            name="search_index_coverage",
            func=SearchIndexCoverageTool(self.search_repo).run,
            description="Checks if the search index contains all the products it should."
        )
        self.register_tool(
            name="capability_mapping",
            func=CatalogCapabilityMappingTool(self.repo).run,
            description="Takes the findings from other tools and maps them to the specific business capabilities that are affected."
        )
    
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

    # Extract context data
    context_data_match = re.search(r'<JSON_DATA_CONTEXT>(.*)</JSON_DATA_CONTEXT>', E['context'], re.DOTALL)
    if context_data_match:
        try:
            E['context_data'] = json.loads(context_data_match.group(1).strip())
        except json.JSONDecodeError:
            pass # Keep as empty dict on error

    # Extract event data (JSONL)
    events_data_match = re.search(r'<JSON_DATA_EVENTS>(.*)</JSON_DATA_EVENTS>', E['context'], re.DOTALL)
    if events_data_match:
        events_jsonl_str = events_data_match.group(1).strip()
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
  "overall_status": "string",
  "root_cause": "string",
  "affected_capabilities": ["string"],
  "summary": "string",
  "detailed_evidence": ["string"],
  "executed_tools": ["string"]
}
```
**CRITICAL**: Do NOT output any text other than the Python code for each turn. Your final turn MUST be only the `print(json.dumps(final_report))` statement.
"""