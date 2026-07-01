import asyncio
import json
import os
import sys
import logging
from typing import Any, Dict, Callable # Added Callable

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from base_agent import BaseAgent
# from .Tools.reindex_trigger_tool import SemanticReindexTriggerTool
# from .Tools.vector_refresh_tool import VectorRefreshTool
# from .Tools.semantic_rules_tool import SemanticRulesTool
from .Tools.vector_refresh_tool import VectorRefreshTool
from .Tools.reindex_trigger_tool import SemanticReindexTriggerTool
from .Tools.semantic_rules_tool import SemanticRulesTool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticFixProposalAgent(BaseAgent):
    """
    Proposes and executes fixes for semantic index issues.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        super().__init__(model_name=model_name, enable_deep_rca=True)
        self._register_tools()

    def _register_tools(self):
        self.register_tool(
            name="vector_refresh",
            func=VectorRefreshTool().run,
            description="Refreshes embeddings for a specific list of SKUs."
        )
        self.register_tool(
            name="semantic_reindex_trigger",
            func=SemanticReindexTriggerTool().run,
            description="Triggers a job to re-index the semantic vector database."
        )
        self.register_tool(
            name="semantic_rules",
            func=SemanticRulesTool().run,
            description="Deploys semantic rules to improve search relevance."
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
*   `Embedding drift detected`: Call `vector_refresh`.
*   `Vector DB health issue`: Report the issue; no tool can fix this.
*   `Semantic coverage gap`: Call `semantic_reindex_trigger`.

**FINAL JSON OUTPUT SCHEMA:**
Your final print MUST be a JSON object.
"""

async def main():
    agent = SemanticFixProposalAgent()
    rca_data = {"root_cause": "Embedding drift detected for 'running shoes' category."}
    result = await agent.run_agent(rca_data)
    print("Agent Output:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
