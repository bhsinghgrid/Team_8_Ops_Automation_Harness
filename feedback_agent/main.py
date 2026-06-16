import os
import json
import argparse
import logging
import datetime
import asyncio
from typing import Dict, Any

from feedback_agent.config import MOCK_MODE
from feedback_agent.db import OCSDatabase
from feedback_agent.agents.fix_verification import FixVerificationAgent
from feedback_agent.agents.metric_comparison import MetricComparisonAgent
from feedback_agent.agents.canary_evaluation import CanaryEvaluationAgent
from feedback_agent.agents.threshold_update import ThresholdUpdateAgent
from feedback_agent.agents.audit_trail import AuditTrailAgent

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('feedback_agent.log', mode='w')
        ]
    )

def run_fallback_pipeline(input_path: str, output_path: str, input_data: dict, query: str):
    logger = logging.getLogger("feedback_agent.orchestrator.fallback")
    logger.info("Executing sequential Python feedback pipeline fallback...")

    db = OCSDatabase()
    agents = [
        ("verification", FixVerificationAgent(db)),
        ("metrics", MetricComparisonAgent(db)),
        ("decision", CanaryEvaluationAgent(db)),
        ("threshold_updates", ThresholdUpdateAgent(db)),
        ("audit_record", AuditTrailAgent(db))
    ]

    pipeline_state: Dict[str, Any] = {}
    for name, agent in agents:
        logger.info(f"Executing sub-agent fallback: {agent.__class__.__name__}")
        try:
            agent_output = agent.run(input_data, pipeline_state)
            pipeline_state.update(agent_output)
        except Exception as e:
            logger.exception(f"Error during fallback execution of sub-agent {agent.__class__.__name__}:")
            pipeline_state[name] = {"error": str(e), "passed": False}

    feedback_result = {
        "agent": "FeedbackAgent",
        "status": "ok" if pipeline_state.get("verification", {}).get("allPassed", False) else "degraded",
        "query": query,
        "timestamp": datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        "verification": pipeline_state.get("verification"),
        "metrics": pipeline_state.get("metrics"),
        "decision": pipeline_state.get("decision"),
        "thresholdUpdates": pipeline_state.get("thresholdUpdates"),
        "auditRecord": pipeline_state.get("auditRecord")
    }

    try:
        with open(output_path, 'w') as f:
            json.dump(feedback_result, f, indent=2)
        logger.info(f"Fallback feedback pipeline completed successfully. Output saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write fallback output JSON to {output_path}: {e}")

    db.close()

def run_feedback_pipeline(input_path: str, output_path: str):
    logger = logging.getLogger("feedback_agent.orchestrator")
    logger.info("Initializing OCS Feedback Agent Pipeline...")
    logger.info(f"Execution Mode: {'MOCK/SIMULATED' if MOCK_MODE else 'LIVE'}")

    if not os.path.exists(input_path):
        logger.error(f"Input file not found at: {input_path}")
        return

    try:
        with open(input_path, 'r') as f:
            input_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read/parse input JSON file: {e}")
        return

    query = input_data.get("query") or input_data.get("result", {}).get("query", "")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not gemini_key:
        logger.warning("GEMINI_API_KEY not configured. To enable agentic orchestration using Gemini, "
                       "set the GEMINI_API_KEY environment variable. Visiting "
                       "https://aistudio.google.com/app/api-keys can help you configure a key.")
        run_fallback_pipeline(input_path, output_path, input_data, query)
        return

    # Agentic Mode using Google Antigravity SDK
    logger.info("GEMINI_API_KEY detected. Launching Google Antigravity Agentic Pipeline...")
    
    db = OCSDatabase()
    verification_agent = FixVerificationAgent(db)
    metrics_agent = MetricComparisonAgent(db)
    eval_agent = CanaryEvaluationAgent(db)
    threshold_agent = ThresholdUpdateAgent(db)
    audit_agent = AuditTrailAgent(db)

    pipeline_state: Dict[str, Any] = {}

    def verify_fix() -> dict:
        """Verifies if the OCS config patches are active.
        
        Returns:
            A dictionary with verification report details (allPassed, checks list).
        """
        logger.info("[AGENTIC TOOL] verify_fix triggered")
        res = verification_agent.run(input_data, pipeline_state)
        pipeline_state.update(res)
        return res

    def compare_metrics() -> dict:
        """Measures search telemetry metrics deltas (zero result rate, latency, relevance).
        
        Returns:
            A dictionary with metrics comparison report.
        """
        logger.info("[AGENTIC TOOL] compare_metrics triggered")
        res = metrics_agent.run(input_data, pipeline_state)
        pipeline_state.update(res)
        return res

    def evaluate_canary() -> dict:
        """Evaluates canary results, shadow testing S2N, and guardrails to make a promote/rollback/hold decision.
        
        Returns:
            A dictionary with the decision report.
        """
        logger.info("[AGENTIC TOOL] evaluate_canary triggered")
        res = eval_agent.run(input_data, pipeline_state)
        pipeline_state.update(res)
        return res

    def update_thresholds() -> dict:
        """Updates watchlist statuses, logs runbook durations, and adjusts signal sensitivities in the DB.
        
        Returns:
            A dictionary with threshold updates details.
        """
        logger.info("[AGENTIC TOOL] update_thresholds triggered")
        res = threshold_agent.run(input_data, pipeline_state)
        pipeline_state.update(res)
        return res

    def write_audit_trail() -> dict:
        """Writes the final immutable audit record to the database ledger.
        
        Returns:
            A dictionary with audit record details.
        """
        logger.info("[AGENTIC TOOL] write_audit_trail triggered")
        res = audit_agent.run(input_data, pipeline_state)
        pipeline_state.update(res)
        return res

    from google.antigravity import Agent, LocalAgentConfig
    from feedback_agent.models import FeedbackResultSchema

    config = LocalAgentConfig(
        model="gemini-3.5-flash",
        api_key=gemini_key,
        tools=[verify_fix, compare_metrics, evaluate_canary, update_thresholds, write_audit_trail],
        response_schema=FeedbackResultSchema,
        system_instructions=(
            "You are the OCS Feedback Orchestrator Agent. Your task is to evaluate the search engine fix "
            "applied for the query. You must run the evaluation pipeline by executing your tools "
            "sequentially in the following order: verify_fix, compare_metrics, evaluate_canary, "
            "update_thresholds, and write_audit_trail. Once all tools finish, synthesize their outputs "
            "into a final FeedbackResultSchema."
        )
    )

    async def run_agentic_flow():
        async with Agent(config) as agent:
            prompt = (
                f"Evaluate the OCS search fix for query '{query}' from the input plan. "
                "Expose all metric observations, decisions, and database actions."
            )
            response = await agent.chat(prompt)
            return await response.structured_output()

    try:
        structured_data = asyncio.run(run_agentic_flow())
        if structured_data:
            # Inject dynamic ISO timestamp if agent output is missing or needs refresh
            if not structured_data.get("timestamp"):
                structured_data["timestamp"] = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
            
            with open(output_path, 'w') as f:
                json.dump(structured_data, f, indent=2)
            logger.info(f"Agentic feedback pipeline completed successfully. Output saved to {output_path}")
        else:
            raise ValueError("Agent returned empty or unparseable structured output.")
    except Exception as e:
        logger.exception("Failed to run agentic workflow, falling back to sequential Python loop:")
        run_fallback_pipeline(input_path, output_path, input_data, query)

    db.close()


if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(description="OCS Feedback Agent Pipeline Orchestrator")
    parser.add_argument("--input", default="input.json", help="Path to input.json from FixPlanAgent")
    parser.add_argument("--output", default="feedback_result.json", help="Path to write feedback_result.json")
    args = parser.parse_args()

    run_feedback_pipeline(args.input, args.output)
