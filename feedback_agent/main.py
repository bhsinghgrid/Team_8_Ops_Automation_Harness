import os
import json
import argparse
import logging
import datetime
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

def run_feedback_pipeline(input_path: str, output_path: str):
    logger = logging.getLogger("feedback_agent.orchestrator")
    logger.info("Initializing OCS Feedback Agent Pipeline...")
    logger.info(f"Execution Mode: {'MOCK/SIMULATED' if MOCK_MODE else 'LIVE'}")

    # 1. Load input.json
    if not os.path.exists(input_path):
        logger.error(f"Input file not found at: {input_path}")
        return

    try:
        with open(input_path, 'r') as f:
            input_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read/parse input JSON file: {e}")
        return

    # 2. Initialize Database connection
    db = OCSDatabase()

    # 3. Instantiate Sub-Agents
    agents = [
        ("verification", FixVerificationAgent(db)),
        ("metrics", MetricComparisonAgent(db)),
        ("decision", CanaryEvaluationAgent(db)),
        ("threshold_updates", ThresholdUpdateAgent(db)),
        ("audit_record", AuditTrailAgent(db))
    ]

    pipeline_state: Dict[str, Any] = {}

    # 4. Sequentially run sub-agents
    for name, agent in agents:
        logger.info(f"Executing sub-agent: {agent.__class__.__name__}")
        try:
            agent_output = agent.run(input_data, pipeline_state)
            # Merge agent output into the accumulated state
            pipeline_state.update(agent_output)
        except Exception as e:
            logger.exception(f"Error during execution of sub-agent {agent.__class__.__name__}:")
            # For robustness, proceed with empty fallback state block if one agent crashes
            pipeline_state[name] = {"error": str(e), "passed": False}

    # 5. Build final feedback_result.json matching the target schema
    feedback_result = {
        "agent": "FeedbackAgent",
        "status": "ok" if pipeline_state.get("verification", {}).get("allPassed", False) else "degraded",
        "query": input_data.get("query") or input_data.get("result", {}).get("query", ""),
        "timestamp": datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        "verification": pipeline_state.get("verification"),
        "metrics": pipeline_state.get("metrics"),
        "decision": pipeline_state.get("decision"),
        "thresholdUpdates": pipeline_state.get("thresholdUpdates"),
        "auditRecord": pipeline_state.get("auditRecord")
    }

    # 6. Save result to output path
    try:
        with open(output_path, 'w') as f:
            json.dump(feedback_result, f, indent=2)
        logger.info(f"Feedback pipeline completed successfully. Output saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output JSON to {output_path}: {e}")

    # 7. Close Database connection
    db.close()

if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(description="OCS Feedback Agent Pipeline Orchestrator")
    parser.add_argument("--input", default="input.json", help="Path to input.json from FixPlanAgent")
    parser.add_argument("--output", default="feedback_result.json", help="Path to write feedback_result.json")
    args = parser.parse_args()

    run_feedback_pipeline(args.input, args.output)
