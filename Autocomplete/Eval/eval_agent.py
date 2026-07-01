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
from .Tools.autocomplete_metrics_tool import AutocompleteMetricsTool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutocompleteEvalAgent(BaseAgent):
    """
    Evaluates the success of an autocomplete fix by analyzing suggestion CTR and regressions.
    """
    def __init__(self, model_name="gemini-1.5-flash"):
        super().__init__(model_name=model_name)
        
        self.metrics_tool = AutocompleteMetricsTool()
        self.register_tool(
            name="evaluate_autocomplete_metrics", 
            func=self.metrics_tool.run, 
            description="Analyzes a report comparing baseline and shadow autocomplete suggestions to evaluate suggestion quality, CTR, and regressions."
        )

    async def run_agent(self, eval_input: dict) -> dict:
        """
        Runs the evaluation agent, orchestrating shadow testing and metrics calculation for autocomplete.
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
            "query": original_signal.get('description', 'generic autocomplete query'),
            "baseline_metrics": {"ctr": 0.05, "coverage": 0.80, "relevance": 0.70},
            "shadow_metrics": {"ctr": 0.06, "coverage": 0.85, "relevance": 0.75},
            "regressions_found": 0 # Assume no regressions for this mock
        }

        # --- Call Metrics Evaluator Tool ---
        metrics_evaluation_output = await self.metrics_tool.run(comparison_report)

        # --- Analyze Metrics and Make Decision ---
        overall_status = metrics_evaluation_output.get("status", "failed")
        decision = metrics_evaluation_output.get("decision", "ROLLBACK_FIX")
        regression_risk = "low" # Placeholder for now, could be derived from metrics
        summary = metrics_evaluation_output.get("summary", "Evaluation completed with generic results.")
        metrics = {
            "ctr_change": metrics_evaluation_output.get("metrics", {}).get("ctr_change", 0.0),
            "regressions_found": metrics_evaluation_output.get("metrics", {}).get("regressions_found", 0)
        }

        return {
            "overall_status": overall_status,
            "decision": decision,
            "regression_risk": regression_risk,
            "summary": summary,
            "metrics": metrics
        }
        return """
        You are a Release Evaluation Agent for an E-commerce Search team, specializing in autocomplete suggestions. Your role is to evaluate the success of a proposed fix based on provided RCA and Fix Proposal results, and then generate a decision and a comprehensive evaluation report. You will leverage a shadow testing framework for this.

**CORE PROTOCOL: EVALUATE & DECIDE.**
Your only role is to analyze the provided `rca_result`, `fix_result`, and `original_signal` (available in `E['state']`) to make an informed decision. You MUST use the `evaluate_autocomplete_metrics` tool with the appropriate data to get quantitative evaluation metrics.

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
    # Prepare a mock comparison_report structure based on original_signal for the AutocompleteMetricsTool.
    # This is a simplification; in a real shadow test, champion and challenger would run.
    comparison_report = {
        "query": original_signal.get('description', 'generic autocomplete query'),
        "baseline_metrics": {"ctr": 0.05, "coverage": 0.80, "relevance": 0.70},
        "shadow_metrics": {"ctr": 0.06, "coverage": 0.85, "relevance": 0.75},
        "regressions_found": 0 # Assume no regressions for this mock
    }
    
    # Now call the tool to evaluate these metrics.
    E['state']['metrics_evaluation_output'] = await evaluate_autocomplete_metrics(comparison_report)
    # DO NOT print the state here. Only call tools or print final output.
    ```
2.  **Analyze & Decide:** Analyze `E['state']['metrics_evaluation_output']` to determine the `overall_status`, `decision`, `regression_risk`, and `summary`. Make sure to base the decision on CTR change and regressions found.
3.  **Finalize:** On your final turn, generate code to construct and print the final JSON output from `E['state']` that strictly conforms to the `EvalOutput` schema. You MUST include `overall_status`, `decision`, `regression_risk`, `summary`, and the `metrics` including `ctr_change` and `regressions_found`.

**FINAL JSON OUTPUT SCHEMA (Strictly Enforced):**
Your final print MUST be a `print(json.dumps(your_dict))` call. The dictionary MUST conform to this `EvalOutput` schema.
```json
{
    "overall_status": "success | failed",
    "decision": "PROMOTE_TO_CANARY | ROLLBACK_FIX",
    "regression_risk": "low | medium | high",
    "summary": "A concise justification of your decision based on the metrics. Mention the CTR change and regression count.",
    "metrics": {
        "ctr_change": "float",
        "regressions_found": "int"
    }
}
```
**CRITICAL**: Do NOT output any text other than the Python code for each turn. Your final turn MUST be only the `print(json.dumps(final_report))` statement."""

# The run_agent method is inherited from BaseAgent.

# =========================
# MAIN
# =========================
async def main():
    print("\n🚀 Running Autocomplete Eval Agent...\n")
    agent = AutocompleteEvalAgent()
    
    # In a real pipeline, this signal would come from the Fix Proposal agent,
    # containing the results of a shadow test.
    input_signal = {
        "description": "Evaluation of a fix for irrelevant suggestions for the query 'shirt'.",
        "diff_id": "autocomplete-diff-12345",
        "context": "The fix involved updating the typo dictionary and re-ranking models."
    }

    result = await agent.run_agent(input_signal)
    
    print("\n📦 FINAL AUTOCOMPLETE EVALUATION REPORT:\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
