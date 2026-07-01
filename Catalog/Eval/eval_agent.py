import asyncio
import json
import os
import sys
from dataclasses import dataclass
import logging
from typing import Callable
import inspect

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from base_agent import BaseAgent
# from .Tools.diffy_api_tool import DiffyApiTool
from .Tools.metrics_evaluator_tool import MetricsEvaluatorTool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EvalOutput:
    overall_status: str
    decision: str
    regression_risk: str
    summary: str

class GoogleEvalAgent(BaseAgent):
    """
    Evaluates the success of a fix by analyzing traffic comparison reports.
    """
    def __init__(self, model_name="gemini-2.5-flash"):
        super().__init__(model_name=model_name, enable_deep_rca=False)
        
        self.metrics_tool = MetricsEvaluatorTool()

        self.register_tool(
            name="evaluate_metrics", 
            func=self.metrics_tool.run, 
            description="Calculates NDCG and other relevance metrics from production and candidate results."
        )

    async def run_agent(self, eval_input: dict) -> dict:
        """
        Runs the evaluation agent, orchestrating shadow testing and metrics calculation.
        """
        # Extract inputs
        fix_result = eval_input.get("fix_result", {})
        rca_result = eval_input.get("rca_result", {})
        original_signal = eval_input.get("original_signal", {})

        # --- Simulate Shadow Testing Data Generation ---
        # In a real scenario, the ShadowTestEngine would run champion and challenger
        # against `original_signal` and produce a comprehensive diffy_report.
        # For this demonstration, we'll create a mock diffy_report.

        # Dynamically generate mock execution results based on the original signal
        execution_results = []
        for i, event in enumerate(original_signal.get('events', [])):
            query_text = event.get('query', {}).get('text', f"query_{i}")
            # Example: derive expected_skus from a known good state or RCA hints
            # For simplicity, using dummy SKUs for now.
            expected_skus = [f"PROD-{i+1:03d}", f"PROD-{i+2:03d}"]
            baseline_top_k = [f"PROD-{i+1:03d}", f"PROD-{i+3:03d}", f"PROD-{i+5:03d}"] # Simulate champion output
            shadow_top_k = [f"PROD-{i+1:03d}", f"PROD-{i+2:03d}", f"PROD-{i+4:03d}"] # Simulate challenger output (improved)
            
            execution_results.append({
                "query_text": query_text,
                "expected_skus": expected_skus,
                "baseline_top_k": baseline_top_k,
                "shadow_top_k": shadow_top_k,
                "query_id": f"q_{i}"
            })
        
        # Simulate latency results
        latency_results = {"baseline_ms": [120, 115, 130, 125, 118], "shadow_ms": [110, 105, 120, 115, 108]}

        mock_diffy_report = {
            "execution_results": execution_results,
            "latency_results": latency_results,
            "diff_id": "mock-eval-report-123"
        }
        
        # --- Call Metrics Evaluator Tool ---
        # Pass the mock diffy_report to the evaluate_metrics tool.
        metrics_evaluation_output = await self.metrics_tool.run({"diffy_report": mock_diffy_report})

        # --- Analyze Metrics and Make Decision ---
        overall_status = metrics_evaluation_output.get("status", "failed")
        decision = metrics_evaluation_output.get("decision", "ROLLBACK_FIX")
        regression_risk = "low" # Placeholder for now, could be derived from metrics
        summary = metrics_evaluation_output.get("summary", "Evaluation completed with generic results.")
        metrics = metrics_evaluation_output.get("metrics", {})

        return {
            "overall_status": overall_status,
            "decision": decision,
            "regression_risk": regression_risk,
            "summary": summary,
            "metrics": metrics
        }
        return """You are a Release Evaluation Agent in a Python REPL environment. Your role is to evaluate the success of a proposed fix based on provided RCA and Fix Proposal results, and then generate a decision and a comprehensive evaluation report. You will leverage a shadow testing framework for this.

**CORE PROTOCOL: EVALUATE & DECIDE.**
Your only role is to analyze the provided `rca_result`, `fix_result`, and `original_signal` (available in `E['state']`) to make an informed decision. You MUST use the `evaluate_metrics` tool with the appropriate data to get quantitative evaluation metrics.

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
    # Prepare a mock diffy_report structure based on original_signal for the MetricsEvaluatorTool.
    # This is a simplification; in a real shadow test, champion and challenger would run.
    # For this demo, we assume 'fix_result' is the 'shadow' and 'rca_result' helps define 'expected_skus'.
    # This part needs careful alignment with how your actual shadow tests generate diffy_report.
    execution_results = []
    for event in original_signal.get('events', []):
        query_text = event.get('query', {}).get('text', '')
        # Simulate champion (baseline) and challenger (fixed) responses.
        # This is a critical point for realistic shadow testing integration.
        # For now, we'll use dummy data or derive from rca_result/fix_result.
        # Ideally, `ShadowTestEngine` would run both champion and challenger on original_signal and produce these.
        baseline_top_k = [f"PROD-{i}" for i in range(100, 106)] # Dummy baseline
        shadow_top_k = [f"PROD-{i}" for i in range(101, 107)] # Dummy shadow (slightly different)
        expected_skus = [f"PROD-{i}" for i in range(100, 103)] # Dummy expected relevant
        execution_results.append({
            "query_text": query_text,
            "expected_skus": expected_skus,
            "baseline_top_k": baseline_top_k,
            "shadow_top_k": shadow_top_k
        })
    
    # Simulate latency results
    latency_results = {"baseline_ms": [100, 110, 105], "shadow_ms": [95, 105, 100]}

    E['diffy_report'] = {
        "execution_results": execution_results,
        "latency_results": latency_results
    }
    
    # Now call the tool to evaluate these metrics.
    E['state']['metrics_evaluation_output'] = await evaluate_metrics(E['diffy_report'])
    # DO NOT print the state here. Only call tools or print final output.
    ```
2.  **Analyze & Decide:** Analyze `E['state']['metrics_evaluation_output']` to determine the `overall_status`, `decision`, `regression_risk`, and `summary`.
3.  **Finalize:** On your final turn, generate code to construct and print the final JSON output from `E['state']` that strictly conforms to the `EvalOutput` schema. You MUST include `overall_status`, `decision`, `regression_risk`, `summary`, and the `ndcg@10` metric.

**FINAL JSON OUTPUT SCHEMA (Strictly Enforced):**
Your final print MUST be a `print(json.dumps(your_dict))` call. The dictionary MUST conform to this `EvalOutput` schema.
```json
{
    "overall_status": "success | failed",
    "decision": "PROMOTE_TO_CANARY | ROLLBACK_FIX",
    "regression_risk": "low | medium | high",
    "summary": "A concise justification of your decision based on the metrics.",
    "metrics": {
        "relevance": { "baseline": { "ndcg@10": "float" }, "shadow": { "ndcg@10": "float" }, "absolute_ndcg_improvement": "float" },
        "performance": { "p995_baseline_ms": "float", "p995_shadow_ms": "float", "p995_latency_increase_ms": "float" }
    }
}
```
**CRITICAL**: Do NOT output any text other than the Python code for each turn. Your final turn MUST be only the `print(json.dumps(final_report))` statement."""

    # The run_agent method is inherited from BaseAgent and does not need to be redefined.

# =========================
# MAIN
# =========================
async def main():
    print("\n🚀 Running Eval Agent (Diffy API Evaluator)...\n")
    agent = GoogleEvalAgent()
    
    # In a real pipeline, this would receive the Diffy report ID from a CI/CD job
    # This mock ID will trigger the mock response in the DiffyApiTool
    input_signal = {
        "diff_id": "c28b-4b1e-b3f9-7153d3e690f3", 
        "context": "Catalog coverage gap patched for Trailhead XT footwear."
    }

    result = await agent.run_agent(input_signal)
    
    print("\n📦 FINAL EVALUATION REPORT:\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())