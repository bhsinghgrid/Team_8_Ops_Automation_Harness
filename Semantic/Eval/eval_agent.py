import asyncio
import json
import os
import sys
import logging

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from base_agent import BaseAgent
from .Tools.semantic_similarity_tool import SemanticSimilarityTool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticEvalAgent(BaseAgent):
    """
    Evaluates the success of a semantic search fix by analyzing the cosine
    similarity between the query and the results.
    """
    def __init__(self, model_name="gemini-1.5-flash"):
        super().__init__(model_name=model_name)
        
        self.metrics_tool = SemanticSimilarityTool()
        self.register_tool(
            name="evaluate_semantic_similarity", 
            func=self.metrics_tool.run, 
            description="Analyzes a report to compare the cosine similarity of results for a baseline (production) and shadow (candidate) search system."
        )

    async def run_agent(self, eval_input: dict) -> dict:
        """
        Runs the evaluation agent, orchestrating shadow testing and metrics calculation for semantic search.
        """
        # Extract inputs
        fix_result = eval_input.get("fix_result", {})
        rca_result = eval_input.get("rca_result", {})
        original_signal = eval_input.get("original_signal", {})

        # --- Simulate Shadow Testing Data Generation ---
        # In a real scenario, the ShadowTestEngine would run champion and challenger
        # against `original_signal` and produce a comprehensive comparison_report.
        # For this demonstration, we'll create a mock comparison_report.

        # Dynamically generate mock comparison data based on the original signal or fix_result
        # This should reflect the RCA findings and expected impact of the fix
        comparison_report = {
            "query": original_signal.get('description', 'generic semantic query'),
            "baseline_metrics": {"average_similarity": 0.70, "relevant_results_count": 10},
            "shadow_metrics": {"average_similarity": 0.75, "relevant_results_count": 12},
            "queries_with_degraded_similarity": 0 # Assume no regressions for this mock
        }

        # --- Call Metrics Evaluator Tool ---
        metrics_evaluation_output = await self.metrics_tool.run(comparison_report)

        # --- Analyze Metrics and Make Decision ---
        overall_status = metrics_evaluation_output.get("status", "failed")
        decision = metrics_evaluation_output.get("decision", "ROLLBACK_FIX")
        regression_risk = "low" # Placeholder for now, could be derived from metrics
        summary = metrics_evaluation_output.get("summary", "Evaluation completed with generic results.")
        metrics = {
            "average_similarity_change": metrics_evaluation_output.get("metrics", {}).get("average_similarity_change", 0.0),
            "queries_with_degraded_similarity": metrics_evaluation_output.get("metrics", {}).get("queries_with_degraded_similarity", 0)
        }

        return {
            "overall_status": overall_status,
            "decision": decision,
            "regression_risk": regression_risk,
            "summary": summary,
            "metrics": metrics
        }
        return """
        You are a Release Evaluation Agent for an E-commerce Search team, specializing in semantic search relevance. Your role is to evaluate the success of a proposed fix based on provided RCA and Fix Proposal results, and then generate a decision and a comprehensive evaluation report. You will leverage a shadow testing framework for this.

**CORE PROTOCOL: EVALUATE & DECIDE.**
Your only role is to analyze the provided `rca_result`, `fix_result`, and `original_signal` (available in `E['state']`) to make an informed decision. You MUST use the `evaluate_semantic_similarity` tool with the appropriate data to get quantitative evaluation metrics.

**ENVIRONMENT & STATE:**
- You are in a Python REPL environment `E`.
- `E['state']` contains `rca_result` (output from RCA agent), `fix_result` (output from Fix Proposal agent), and `original_signal` (the initial signal that triggered the workflow).
- You MUST manage all findings and intermediate results in `E['state']`.

**EXECUTION LOOP (CODE ONLY):**
1.  **Initialize & Extract Data:**
    ```python
    import json
    # The eval_input (containing rca_result, fix_result, original_signal) is directly passed to run_agent.
    # So, E['state'] should already be initialized with these.
    # Ensure `rca_result` and `fix_result` are accessible.
    rca_result = E['state']['rca_result']
    fix_result = E['state']['fix_result']
    original_signal = E['state']['original_signal']
    # Prepare a mock comparison_report structure based on original_signal for the SemanticSimilarityTool.
    # This is a simplification; in a real shadow test, champion and challenger would run.
    comparison_report = {
        "query": original_signal.get('description', 'generic semantic query'),
        "baseline_metrics": {"average_similarity": 0.70, "relevant_results_count": 10},
        "shadow_metrics": {"average_similarity": 0.75, "relevant_results_count": 12},
        "queries_with_degraded_similarity": 0 # Assume no regressions for this mock
    }
    
    # Now call the tool to evaluate these metrics.
    E['state']['metrics_evaluation_output'] = await evaluate_semantic_similarity(comparison_report)
    # DO NOT print the state here. Only call tools or print final output.
    ```
2.  **Analyze & Decide:** Analyze `E['state']['metrics_evaluation_output']` to determine the `overall_status`, `decision`, `regression_risk`, and `summary`. Make sure to base the decision on average similarity change and queries with degraded similarity.
3.  **Finalize:** On your final turn, generate code to construct and print the final JSON output from `E['state']` that strictly conforms to the `EvalOutput` schema. You MUST include `overall_status`, `decision`, `regression_risk`, `summary`, and the `metrics` including `average_similarity_change` and `queries_with_degraded_similarity`.

**FINAL JSON OUTPUT SCHEMA (Strictly Enforced):**
Your final print MUST be a `print(json.dumps(your_dict))` call. The dictionary MUST conform to this `EvalOutput` schema.
```json
{
    "overall_status": "success | failed",
    "decision": "PROMOTE_TO_CANARY | ROLLBACK_FIX",
    "regression_risk": "low | medium | high",
    "summary": "A concise justification of your decision based on the cosine similarity change.",
    "metrics": {
        "average_similarity_change": "float",
        "queries_with_degraded_similarity": "int"
    }
}
```
**CRITICAL**: Do NOT output any text other than the Python code for each turn. Your final turn MUST be only the `print(json.dumps(final_report))` statement."""

# The run_agent method is inherited from BaseAgent.

# =========================
# MAIN
# =========================
async def main():
    print("\n🚀 Running Semantic Eval Agent...\n")
    agent = SemanticEvalAgent()
    
    input_signal = {
        "description": "Evaluation of a fix for low relevance for the query 'red running shoes'.",
        "diff_id": "semantic-diff-67890",
        "context": "The fix involved retraining the product embedding model."
    }

    result = await agent.run_agent(input_signal)
    
    print("\n📦 FINAL SEMANTIC EVALUATION REPORT:\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
