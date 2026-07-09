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
from .Tools.embedding_fine_tuning_tool import EmbeddingFineTuningTool
from .Tools.query_expansion_rule_tool import QueryExpansionRuleTool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticFixProposalAgent(BaseAgent):
    """
    Proposes and executes fixes for semantic index issues.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        super().__init__(model_name=model_name, enable_deep_rca=True)
        self.fine_tuning_tool = EmbeddingFineTuningTool()
        self.query_expansion_tool = QueryExpansionRuleTool()
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
        self.register_tool(
            name="fine_tune_embedding_model",
            func=self.fine_tuning_tool.run,
            description="Triggers a fine-tuning job for a specified embedding model using new training data."
        )
        self.register_tool(
            name="upsert_query_expansion_rule",
            func=self.query_expansion_tool.run,
            description="Adds or updates a query expansion rule for semantic search."
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

**ROOT CAUSE TO TOOL MAPPING (Match exact terms or semantic meanings):**
*   `Embedding drift detected` or any system anomaly of type `backend_server_error`: Call `vector_refresh`.
*   `Vector DB health issue`: Report the issue; no tool can fix this.
*   `Semantic coverage gap`: Call `semantic_reindex_trigger`.
*   `Embedding model outdated`: Call `fine_tune_embedding_model` with updated training data.
*   `Suboptimal query understanding` or typo issues: Call `upsert_query_expansion_rule` to refine semantic query interpretation.
*   For any unknown issues, call `run_deep_rca_investigation`.

**SYNTAX SAFEGUARDS:**
- ALWAYS use double-quotes (`"`) for outer string literals and single-quotes (`'`) for nested strings to avoid compile-time Python SyntaxErrors. E.g. write `"System anomaly of type 'backend_server_error'."`

**FINAL JSON OUTPUT SCHEMA:**
Your final print MUST be a JSON object."""

async def main():
    agent = SemanticFixProposalAgent()
    rca_data = {"root_cause": "Embedding drift detected for 'running shoes' category."}
    result = await agent.run_agent(rca_data)
    print("Agent Output:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
