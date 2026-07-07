import asyncio
import json
import logging
import os
import sys

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from base_agent import BaseAgent
from typing import Any, Dict, Callable # Added Callable

from .Tools.adjust_prefix_weights_tool import AdjustPrefixWeightsTool
from .Tools.boost_popular_entities_tool import BoostPopularEntitiesTool
from .Tools.update_typo_dictionary_tool import UpdateTypoDictionaryTool
from .Tools.dynamic_reranking_tool import DynamicRerankingTool
from .Tools.data_reingestion_tool import DataReingestionTool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutocompleteFixProposalAgent(BaseAgent):
    """
    Proposes and executes fixes for autocomplete issues.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        super().__init__(model_name=model_name, enable_deep_rca=True)
        self.reranking_tool = DynamicRerankingTool()
        self.reingestion_tool = DataReingestionTool()
        self._register_tools()

    def _register_tools(self):
        self.register_tool(
            name="adjust_prefix_weights", 
            func=AdjustPrefixWeightsTool().run, 
            description="Adjusts the weights of prefixes to improve autocomplete relevance."
        )
        self.register_tool(
            name="boost_popular_entities", 
            func=BoostPopularEntitiesTool().run, 
            description="Boosts popular entities in autocomplete suggestions."
        )
        self.register_tool(
            name="update_typo_dictionary", 
            func=UpdateTypoDictionaryTool().run, 
            description="Updates the typo dictionary to improve typo tolerance in autocomplete."
        )
        self.register_tool(
            name="apply_dynamic_reranking", 
            func=self.reranking_tool.run, 
            description="Applies dynamic re-ranking rules to autocomplete suggestions."
        )
        self.register_tool(
            name="trigger_data_reingestion", 
            func=self.reingestion_tool.run, 
            description="Triggers a re-ingestion process for a specified autocomplete data source."
        )

    def get_system_prompt(self) -> str:
        return """You are an RLM Fix-Execution Orchestrator in a Python REPL environment.

**CORE PROTOCOL: ORCHESTRATE, DON'T RE-DIAGNOSE.**
Your only role is to generate Python code to execute the correct fix tool based on the `root_cause` in the context.

**ENVIRONMENT:**
- You are in a REPL environment `E`.
- The Root Cause Analysis report is in the `E['context']` variable.

**EXECUTION LOOP:**
1.  Analyze the `root_cause` from `E['context']`.
2.  Select the appropriate tool based on the mapping below.
3.  Generate Python code to call the tool and print a final JSON report.

**ROOT CAUSE TO TOOL MAPPING:**
*   `missing_typo_synonyms`: Call `update_typo_dictionary`.
*   `prefix_index_stale`: Call `adjust_prefix_weights`.
*   `popularity_bias_low`: Call `boost_popular_entities`.
*   `ranking_discrepancy`: Call `apply_dynamic_reranking` with relevant conditions and boost factors.
*   `stale_autocomplete_data`: Call `trigger_data_reingestion` for the affected data source.

**FINAL JSON OUTPUT SCHEMA:**
Your final print MUST be a JSON object with this schema:
{
    "status": "string",
    "reason": "string",
    "action_proposed": "string",
    "fix_executed": "boolean",
    "next_steps": "string"
}"""

    def format_user_message(self, signal_data: Dict[str, Any]) -> str:
        # Assuming signal_data contains RCA output
        rca_summary = signal_data.get("summary", "No RCA summary provided.")
        return f"Here is the Root Cause Analysis output. Please propose and execute a fix.\\nRCA Summary: {rca_summary}"

async def main():
    agent = AutocompleteFixProposalAgent()
    rca_output = {"root_cause": "The suggestion model is over-weighting unpopular terms.", "summary": "Model bias found."}
    result = await agent.run_agent(rca_output)
    print("Agent Output:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
