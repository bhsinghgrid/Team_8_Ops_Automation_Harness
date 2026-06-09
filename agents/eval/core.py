# Runbook_System_Final/agents/eval/core.py
"""Agent for Phase 3 Evaluation and Shadow Testing."""
import json
import asyncio
from typing import Dict, Any
import httpx # For asynchronous HTTP requests
from Runbook_System_Final.shared.schemas import OpsSignal, RootCauseReport, EvalReport
from Runbook_System_Final.orchestration.rlm_client import RLMClient
from Runbook_System_Final.shadow_testing.shadow_test_agent import run_agent as run_shadow_test

class EvalAgent:
    """
    The EvalAgent runs shadow tests and evaluates the proposed fix,
    providing confidence scores and comparison summaries.
    """
    def __init__(self, rlm_client: RLMClient):
        self.rlm_client = rlm_client # Retain for consistency, even if not directly used here
        print("[EvalAgent]: Initialized (RLMClient for potential future use).")

    async def run(self, signal: OpsSignal, root_cause_report: RootCauseReport) -> EvalReport:
        """Run shadow test comparison and generate evaluation report."""
        print(f"[EvalAgent]: Running evaluation for signal {signal.signal_id}...")

        # --- PHASE 3: SEARCH SHADOW FACTORY (REAL/MOCKED TRAFFIC) ---
        diffy_proxy_url = "http://localhost:31900/search" # Your Diffy Proxy URL
        assessment_state = "pass" # Default to pass
        confidence_score = 0.9 # Default confidence
        shadow_metrics: Dict[str, Any] = {}
        eval_summary = "Shadow test completed (mocked)."

        print(f"  ...simulating search cluster traffic for '{signal.summary}' to Diffy Proxy ({diffy_proxy_url})...")
        await asyncio.sleep(2) # Simulate stabilization time

        try:
            async with httpx.AsyncClient() as client:
                for i in range(5): # Send a few mock requests
                    try:
                        response = await client.get(diffy_proxy_url, timeout=5)
                        print(f"  [EvalAgent]: Mock Diffy request {i+1} status: {response.status_code}")
                    except httpx.ConnectError as e:
                        print(f"  ⚠️ Connection Error to Diffy Proxy: {e}. Diffy might not be running or accessible.")
                        assessment_state = "blocked"
                        eval_summary = f"Shadow testing blocked: Diffy Proxy unreachable. Details: {e}"
                        confidence_score = 0.0
                        break 
                    except Exception as e:
                        print(f"  ⚠️ Other HTTP Error during Diffy interaction: {e}")
                        assessment_state = "fail"
                        eval_summary = f"Shadow testing failed due to HTTP error. Details: {e}"
                        confidence_score = 0.5
                        break
                else: 
                    print("  [EvalAgent]: Mock Diffy traffic generation complete.")

        except Exception as e:
            print(f"  ❌ An unexpected error occurred during HTTP client setup or traffic generation: {e}")
            assessment_state = "blocked"
            eval_summary = f"Shadow testing blocked due to unexpected error: {e}"
            confidence_score = 0.0

        if assessment_state != "blocked": 
            shadow_input = {
                "query": signal.signal_id,
                "shadowTest": {
                    "baseline": {"docs": 5000, "results": 0, "status": "ok"},
                    "candidate": {"docs": 5100, "results": 12, "status": "ok"} 
                }
            }
            
            shadow_output = run_shadow_test(shadow_input)
            result_data = shadow_output.get("result", {})
            assessment = result_data.get("assessment", {})
            
            conf_map = {"high": 0.95, "medium": 0.75, "low": 0.30}
            raw_confidence = result_data.get("confidence", "low") 
            
            confidence_score = conf_map.get(raw_confidence.lower(), 0.0)
            
            assessment_state = assessment.get("state", "unknown")
            eval_summary = assessment.get("summary", "Shadow test completed.")
            shadow_metrics = result_data.get("comparisonSummary", {})

        print(f"[EvalAgent]: Evaluation complete for {signal.signal_id}.")

        return EvalReport(
            signal_id=signal.signal_id,
            assessment_state=assessment_state,
            confidence_score=confidence_score,
            shadow_metrics=shadow_metrics,
            eval_summary=eval_summary
        )
