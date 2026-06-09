# temporal/feedback_activities.py
import os
import sys
import json
import logging
import datetime
from typing import Dict, Any, List
from pathlib import Path
from temporalio import activity

# Use environment variables or static logic instead of resolve() at top level
WORKSPACE_ROOT = Path("/Users/bhsingh/Documents/Backend")
FEEDBACK_ROOT = WORKSPACE_ROOT / "Feedback"

# Helper for path setup
def setup_feedback_paths():
    if str(FEEDBACK_ROOT) not in sys.path:
        sys.path.insert(0, str(FEEDBACK_ROOT))

# Import schemas
from temporal.schemas import Runbook

logger = logging.getLogger(__name__)

def prepare_feedback_input(runbook: Runbook, apply_status: str) -> str:
    """
    Prepares an input.json for the feedback agent based on the Runbook and the result of the apply_fix activity.
    """
    input_template_path = FEEDBACK_ROOT / "input.json"
    target_input_path = WORKSPACE_ROOT / f"input_{runbook.runbook_id}.json"
    
    if input_template_path.exists():
        with open(input_template_path, 'r') as f:
            data = json.load(f)
    else:
        data = {
            "agent": "FixPlanAgent",
            "status": "ok",
            "query": runbook.signal.raw_data.get("query", "unknown query"),
            "result": {}
        }
    
    data["query"] = runbook.signal.raw_data.get("query", "unknown query")
    if "result" not in data:
        data["result"] = {}
    data["result"]["query"] = data["query"]
    
    data["result"]["applyResult"] = {
        "applied": apply_status == "APPLIED",
        "dryRun": False,
        "timestamp": datetime.datetime.now().isoformat(),
        "artifacts": [
            {
                "name": f"patch_{runbook.runbook_id}.json",
                "type": "configuration_patch",
                "path": str(WORKSPACE_ROOT / f"patch_{runbook.runbook_id}.json")
            }
        ]
    }

    if "catalogPatch" not in data["result"]:
        data["result"]["catalogPatch"] = {
            "searchableFields": {"add": ["description", "tags"]},
            "catalogSize": 100
        }
    if "embeddingPatch" not in data["result"]:
        data["result"]["embeddingPatch"] = {
            "refreshEmbeddings": True,
            "affectedProductIds": ["sku-1", "sku-2"]
        }

    with open(target_input_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return str(target_input_path)

@activity.defn
async def run_feedback_agent_activity(*args) -> Dict[str, Any]:
    """
    Runs the Feedback Agent pipeline.
    Expects (runbook_data, apply_status).
    """
    setup_feedback_paths()
    if len(args) == 2:
        runbook_data, apply_status = args
    elif len(args) == 1:
        runbook_data = args[0]
        apply_status = "UNKNOWN"
    else:
        raise ValueError(f"run_feedback_agent_activity expects 2 arguments, got {len(args)}")

    from feedback_agent.main import run_feedback_pipeline
    
    runbook = Runbook.model_validate(runbook_data)
    input_path = prepare_feedback_input(runbook, apply_status)
    output_path = WORKSPACE_ROOT / f"feedback_result_{runbook.runbook_id}.json"
    
    logger.info(f"Running Feedback Agent for Runbook {runbook.runbook_id} with apply_status: {apply_status}")
    
    run_feedback_pipeline(str(input_path), str(output_path))
    
    if output_path.exists():
        with open(output_path, 'r') as f:
            result = json.load(f)
        return result
    else:
        return {"status": "error", "message": "Feedback result not generated"}

@activity.defn
async def run_canary_rollout_activity(*args) -> str:
    """
    Runs the Canary Release Controller.
    Expects (runbook_data, apply_status).
    """
    setup_feedback_paths()
    if len(args) == 2:
        runbook_data, apply_status = args
    elif len(args) == 1:
        runbook_data = args[0]
        apply_status = "UNKNOWN"
    else:
        raise ValueError(f"run_canary_rollout_activity expects 2 arguments, got {len(args)}")

    from feedback_agent.canary.controller import CanaryReleaseController
    
    runbook = Runbook.model_validate(runbook_data)
    input_path = prepare_feedback_input(runbook, apply_status)
    output_dir = WORKSPACE_ROOT / f"canary_output_{runbook.runbook_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Running Canary Rollout for Runbook {runbook.runbook_id} with apply_status: {apply_status}")
    
    controller = CanaryReleaseController(
        input_path=str(input_path),
        output_dir=str(output_dir)
    )
    
    result = controller.run()
    return result.get("status", "FAILED")

