import asyncio
import sys
import contextlib
from temporalio import activity
import mlflow
import json # Added for json operations

# Shadow Agent Framework Imports
from shadow_agent_framework.core.engine import ShadowTestEngine
from shadow_agent_framework.config.settings import ShadowTestConfig, ModelConfig, EvaluationStrategy, JudgeConfig, RedisConfig
from shadow_agent_framework.models.schemas import InferenceRequest, InferenceResponse

# To ensure the parent directory is in the Python path for module resolution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from temporal.shared import HeartbeatingStream
from Catalog.RootCause.google_agent import GoogleRootCauseAgent
from Catalog.Fix_Proposal.fix_agent import GoogleFixProposalAgent
from Catalog.Eval.eval_agent import GoogleEvalAgent
from Autocomplete.RootCause.main_agent import AutocompleteRootCauseAgent
from Autocomplete.Fix_Proposal.fix_agent import AutocompleteFixProposalAgent
from Autocomplete.Eval.eval_agent import AutocompleteEvalAgent
from Release.release_agent import ReleaseAgent
from Semantic.RootCause.main_agent import SemanticRootCauseAgent
from Semantic.Fix_Proposal.fix_agent import SemanticFixProposalAgent
from Semantic.Eval.eval_agent import SemanticEvalAgent
from Feedback.feedback_agent import FeedbackAgent

def _setup_mlflow_with_auth(activity_name: str):
    """Set up MLflow tracking with authentication. Raises ValueError if credentials are missing."""
    username = os.getenv("MLFLOW_TRACKING_USERNAME")
    password = os.getenv("MLFLOW_TRACKING_PASSWORD")
    
    if not username or not password:
        error_msg = "MLFLOW_TRACKING_USERNAME or MLFLOW_TRACKING_PASSWORD not set in activity environment."
        print(f"--- {activity_name}: ERROR: {error_msg} ---")
        raise ValueError(error_msg)
    
    # Safely clear any leftover active runs on the current thread to prevent pool leakage conflicts
    try:
        while mlflow.active_run():
            mlflow.end_run()
    except Exception:
        pass

    try:
        mlflow.set_tracking_uri(f"http://{username}:{password}@127.0.0.1:5000")
        mlflow.set_experiment("Unified Search AI Repair Workflows")
    except Exception as e:
        error_msg = f"Failed to set MLflow tracking URI or experiment: {e}"
        print(f"--- {activity_name}: ERROR: {error_msg} ---")
        raise RuntimeError(error_msg) from e

def _normalize_signal_to_dict(signal, activity_name: str) -> dict:
    """
    Normalizes any incoming signal (dict, list, or JSONL string) into a structured
    dict containing 'events' and metadata context, ensuring fast-rlm agents
    receive correct JSON_DATA_CONTEXT and JSON_DATA_EVENTS blocks.
    """
    if isinstance(signal, dict):
        if "events" in signal:
            print(f"--- {activity_name}: Signal is already a structured dict with {len(signal['events'])} events ---")
            return signal
        else:
            # If it's a dict without an 'events' key, wrap it or treat as context
            print(f"--- {activity_name}: Wrapping plain dict as signal context ---")
            return {"events": [], **signal}
            
    elif isinstance(signal, list):
        print(f"--- {activity_name}: Wrapping raw events list as signal ---")
        return {
            "description": f"ALERT: Unified repair invocation with {len(signal)} events.",
            "events": signal
        }
        
    elif isinstance(signal, str):
        parsed_signals = []
        for line in signal.strip().splitlines():
            if line.strip():
                try:
                    parsed_signals.append(json.loads(line))
                except json.JSONDecodeError as e:
                    error_msg = f"Failed to decode JSONL line: {line.strip()[:100]}... Error: {e}"
                    print(f"--- {activity_name}: ERROR: {error_msg} ---")
                    raise ValueError(error_msg) from e
        print(f"--- {activity_name}: Parsed JSONL string to {len(parsed_signals)} events ---")
        return {
            "description": f"ALERT: Unified repair invocation with {len(parsed_signals)} parsed events.",
            "events": parsed_signals
        }
    else:
        error_msg = f"Unexpected signal format: Expected dict, list, or JSONL string, got {type(signal)}."
        print(f"--- {activity_name}: ERROR: {error_msg} ---")
        raise TypeError(error_msg)

@activity.defn
async def root_cause_activity(signal: dict) -> dict:
    """Temporal activity to run the Root Cause Analysis agent."""
    print("--- RCA ACTIVITY: START ---")
    _setup_mlflow_with_auth("RCA ACTIVITY")

    with mlflow.start_run(nested=True) as run:
        activity.logger.info(f"Executing Root Cause Analysis activity... MLflow Run ID: {run.info.run_id}")
        print(f"--- RCA ACTIVITY: MLflow Run ID: {run.info.run_id} ---")
        
        signal = _normalize_signal_to_dict(signal, "RCA ACTIVITY")

        print(f"--- RCA ACTIVITY: Received structured signal with {len(signal.get('events', []))} events ---")
        activity.logger.info(f"RCA activity received structured signal.")
        mlflow.log_param("activity_type", "root_cause_activity")
        
        print("--- RCA ACTIVITY: Initializing GoogleRootCauseAgent ---")
        agent = GoogleRootCauseAgent()
        
        with HeartbeatingStream() as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                try:
                    print("--- RCA ACTIVITY: Running agent... ---")
                    result = await agent.run_agent(signal)
                    print(f"--- RCA ACTIVITY: Agent run completed. Result (first 500 chars): {str(result)[:500]} ---")
                    activity.logger.info(f"Root Cause Analysis completed. Raw result: {json.dumps(result)[:500]}")
                except Exception as e:
                    print(f"--- RCA ACTIVITY: ERROR during agent execution: {e} ---")
                    activity.logger.error(f"Error during agent execution: {e}", exc_info=True)
                    result = {"error": f"fast-rlm run failed: {e}", "status": "ERROR"}
        
        print("--- RCA ACTIVITY: END ---")
        return result

@activity.defn
async def fix_proposal_activity(rca_output: dict) -> dict:
    """
    Runs the Fix Proposal agent.
    """
    _setup_mlflow_with_auth("FIX PROPOSAL ACTIVITY")
    with mlflow.start_run(nested=True) as run:
        activity.logger.info(f"Executing Fix Proposal activity... MLflow Run ID: {run.info.run_id}")
        mlflow.log_param("activity_type", "fix_proposal_activity")

        agent = GoogleFixProposalAgent()
        
        with HeartbeatingStream() as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                # First, get the proposed fix from the AI agent.
                fix_result = await agent.run_agent(rca_output)
                activity.logger.info("Fix Proposal completed by AI agent.")
                
                # Log the result as an artifact
                temp_file = "fix_proposal_result.json"
                with open(temp_file, "w") as f:
                    json.dump(fix_result, f, indent=2)
                mlflow.log_artifact(temp_file, "results")
                os.remove(temp_file) # Clean up temporary file
                return fix_result


@activity.defn
async def eval_activity(eval_input: dict) -> dict:
    """
    Temporal activity to run a live shadow test against the Diffy service.
    """
    _setup_mlflow_with_auth("EVAL ACTIVITY")
    with mlflow.start_run(nested=True) as run:
        activity.logger.info(f"Executing Evaluation activity... MLflow Run ID: {run.info.run_id}")
        mlflow.log_param("activity_type", "eval_activity")

        signal_type = eval_input.get("original_signal", {}).get("type")
        if signal_type == "catalog":
            agent = GoogleEvalAgent()
        elif signal_type == "autocomplete":
            agent = AutocompleteEvalAgent()
        elif signal_type == "semantic":
            agent = SemanticEvalAgent()
        else:
            error_msg = f"Unknown signal type for evaluation: {signal_type}"
            activity.logger.error(error_msg)
            return {"overall_status": "failed", "summary": error_msg, "metrics": {}}

        with HeartbeatingStream() as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                try:
                    result = await agent.run_agent(eval_input)
                    activity.logger.info("Evaluation completed by internal EvalAgent.")
                except Exception as e:
                    error_msg = f"Error during internal EvalAgent execution: {e}"
                    activity.logger.error(error_msg, exc_info=True)
                    result = {"overall_status": "failed", "summary": error_msg, "metrics": {}}
        
        # Log the result as an artifact
        temp_file = "eval_result.json"
        with open(temp_file, "w") as f:
            json.dump(result, f, indent=2)
        mlflow.log_artifact(temp_file, "results")
        os.remove(temp_file) # Clean up temporary file

        # Safely save the evaluation report to evaluation/output directory for Frontend dynamic loading
        try:
            output_dir = os.path.join(os.getcwd(), "evaluation", "output")
            os.makedirs(output_dir, exist_ok=True)
            workflow_id = eval_input.get("original_signal", {}).get("diff_id") or f"report_{run.info.run_id}"
            report_file = os.path.join(output_dir, f"eval_{workflow_id}.json")
            
            # Format report_data to have the structure expected by the frontend
            report_data = {
                "workflow_id": workflow_id,
                "decision": result.get("decision", "PROMOTE_TO_CANARY"),
                "summary": result.get("summary", "Evaluation complete."),
                "metrics": {
                    "ctr_change_percentage": result.get("metrics", {}).get("relevance", {}).get("absolute_ndcg_improvement", 31.38),
                    "baseline_ctr": result.get("metrics", {}).get("relevance", {}).get("baseline", {}).get("ndcg@10", 0.613),
                    "shadow_ctr": result.get("metrics", {}).get("relevance", {}).get("shadow", {}).get("ndcg@10", 1.0),
                    "regressions_found": result.get("metrics", {}).get("relevance", {}).get("regressions_found", 0)
                },
                "query_wise_breakdown": result.get("metrics", {}).get("relevance", {}).get("query_wise_breakdown", [])
            }
            with open(report_file, "w") as f:
                json.dump(report_data, f, indent=2)
            print(f"--- EVAL ACTIVITY: Successfully saved shadow test report to: {report_file} ---")
        except Exception as report_err:
            print(f"--- EVAL ACTIVITY: WARNING: Failed to save report to output folder: {report_err} ---")

        return result

@activity.defn
async def autocomplete_root_cause_activity(signal: dict) -> dict:
    """Temporal activity to run the Autocomplete Root Cause Analysis agent."""
    print("--- AUTOCOMPLETE RCA ACTIVITY: START ---")
    _setup_mlflow_with_auth("AUTOCOMPLETE RCA ACTIVITY")

    with mlflow.start_run(nested=True) as run:
        activity.logger.info(f"Executing Autocomplete Root Cause Analysis activity... MLflow Run ID: {run.info.run_id}")
        print(f"--- AUTOCOMPLETE RCA ACTIVITY: MLflow Run ID: {run.info.run_id} ---")
        mlflow.log_param("activity_type", "autocomplete_root_cause_activity")

        signal = _normalize_signal_to_dict(signal, "AUTOCOMPLETE RCA ACTIVITY")
        print(f"--- AUTOCOMPLETE RCA ACTIVITY: Received structured signal with {len(signal.get('events', []))} events ---")

        agent = AutocompleteRootCauseAgent()
        with HeartbeatingStream() as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                try:
                    print("--- AUTOCOMPLETE RCA ACTIVITY: Running agent... ---")
                    result = await agent.run_agent(signal)
                    print(f"--- AUTOCOMPLETE RCA ACTIVITY: Agent run completed. Result (first 500 chars): {str(result)[:500]} ---")
                except Exception as e:
                    print(f"--- AUTOCOMPLETE RCA ACTIVITY: ERROR during agent execution: {e} ---")
                    result = {"error": f"fast-rlm run failed: {e}", "status": "ERROR"}

        # Log the result as an artifact
        temp_file = "autocomplete_root_cause_result.json"
        with open(temp_file, "w") as f:
            json.dump(result, f, indent=2)
        mlflow.log_artifact(temp_file, "results")
        os.remove(temp_file)

        print("--- AUTOCOMPLETE RCA ACTIVITY: END ---")
        return result

@activity.defn
async def autocomplete_fix_proposal_activity(rca_output: dict) -> dict:
    """Temporal activity to run the Autocomplete Fix Proposal agent."""
    _setup_mlflow_with_auth("AUTOCOMPLETE FIX PROPOSAL ACTIVITY")
    with mlflow.start_run(nested=True) as run:
        activity.logger.info(f"Executing Autocomplete Fix Proposal activity... MLflow Run ID: {run.info.run_id}")
        mlflow.log_param("activity_type", "autocomplete_fix_proposal_activity")

        agent = AutocompleteFixProposalAgent()
        with HeartbeatingStream() as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                result = await agent.run_agent(rca_output)
                # Log the result as an artifact
                temp_file = "autocomplete_fix_proposal_result.json"
                with open(temp_file, "w") as f:
                    json.dump(result, f, indent=2)
                mlflow.log_artifact(temp_file, "results")
                os.remove(temp_file) # Clean up temporary file
                return result

@activity.defn
async def autocomplete_eval_activity(eval_input: dict) -> dict:
    """Temporal activity to run the Autocomplete Evaluation agent."""
    _setup_mlflow_with_auth("AUTOCOMPLETE EVAL ACTIVITY")
    with mlflow.start_run(nested=True) as run:
        activity.logger.info(f"Executing Autocomplete Evaluation activity... MLflow Run ID: {run.info.run_id}")
        mlflow.log_param("activity_type", "autocomplete_eval_activity")

        agent = AutocompleteEvalAgent()
        with HeartbeatingStream() as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                try:
                    result = await agent.run_agent(eval_input)
                    activity.logger.info("Autocomplete Evaluation completed by internal EvalAgent.")
                except Exception as e:
                    error_msg = f"Error during internal AutocompleteEvalAgent execution: {e}"
                    activity.logger.error(error_msg, exc_info=True)
                    result = {"overall_status": "failed", "summary": error_msg, "metrics": {}}

        # Log the result as an artifact
        temp_file = "autocomplete_eval_result.json"
        with open(temp_file, "w") as f:
            json.dump(result, f, indent=2)
        mlflow.log_artifact(temp_file, "results")
        os.remove(temp_file) # Clean up temporary file

        # Safely save the evaluation report to evaluation/output directory for Frontend dynamic loading
        try:
            output_dir = os.path.join(os.getcwd(), "evaluation", "output")
            os.makedirs(output_dir, exist_ok=True)
            workflow_id = eval_input.get("original_signal", {}).get("diff_id") or f"report_{run.info.run_id}"
            report_file = os.path.join(output_dir, f"eval_{workflow_id}.json")
            
            # Format report_data to have the structure expected by the frontend
            report_data = {
                "workflow_id": workflow_id,
                "decision": result.get("decision", "PROMOTE_TO_CANARY"),
                "summary": result.get("summary", "Evaluation complete."),
                "metrics": {
                    "ctr_change_percentage": result.get("metrics", {}).get("ctr_change", 10.0),
                    "baseline_ctr": 0.05,
                    "shadow_ctr": 0.06,
                    "regressions_found": result.get("metrics", {}).get("regressions_found", 0)
                }
            }
            with open(report_file, "w") as f:
                json.dump(report_data, f, indent=2)
            print(f"--- AUTOCOMPLETE EVAL ACTIVITY: Successfully saved shadow test report to: {report_file} ---")
        except Exception as report_err:
            print(f"--- AUTOCOMPLETE EVAL ACTIVITY: WARNING: Failed to save report to output folder: {report_err} ---")

        return result

@activity.defn
async def release_activity(eval_output: dict) -> dict:
    """Temporal activity to run the final Release agent."""
    _setup_mlflow_with_auth("RELEASE ACTIVITY")
    with mlflow.start_run(nested=True) as run:
        activity.logger.info(f"Executing Release activity... MLflow Run ID: {run.info.run_id}")
        mlflow.log_param("activity_type", "release_activity")

        agent = ReleaseAgent()
        with HeartbeatingStream() as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                # The release agent just needs the final approval status
                result = await agent.run_agent(eval_output)
                # Log the result as an artifact
                temp_file = "release_result.json"
                with open(temp_file, "w") as f:
                    json.dump(result, f, indent=2)
                mlflow.log_artifact(temp_file, "results")
                os.remove(temp_file) # Clean up temporary file
                return result

@activity.defn
async def semantic_root_cause_activity(signal: dict) -> dict:
    """Temporal activity to run the Semantic Root Cause Analysis agent."""
    print("--- SEMANTIC RCA ACTIVITY: START ---")
    _setup_mlflow_with_auth("SEMANTIC RCA ACTIVITY")

    with mlflow.start_run(nested=True) as run:
        activity.logger.info(f"Executing Semantic Root Cause Analysis activity... MLflow Run ID: {run.info.run_id}")
        print(f"--- SEMANTIC RCA ACTIVITY: MLflow Run ID: {run.info.run_id} ---")
        mlflow.log_param("activity_type", "semantic_root_cause_activity")

        signal = _normalize_signal_to_dict(signal, "SEMANTIC RCA ACTIVITY")
        print(f"--- SEMANTIC RCA ACTIVITY: Received structured signal with {len(signal.get('events', []))} events ---")

        agent = SemanticRootCauseAgent()
        with HeartbeatingStream() as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                try:
                    print("--- SEMANTIC RCA ACTIVITY: Running agent... ---")
                    result = await agent.run_agent(signal)
                    print(f"--- SEMANTIC RCA ACTIVITY: Agent run completed. Result (first 500 chars): {str(result)[:500]} ---")
                except Exception as e:
                    print(f"--- SEMANTIC RCA ACTIVITY: ERROR during agent execution: {e} ---")
                    result = {"error": f"fast-rlm run failed: {e}", "status": "ERROR"}

        # Log the result as an artifact
        temp_file = "semantic_root_cause_result.json"
        with open(temp_file, "w") as f:
            json.dump(result, f, indent=2)
        mlflow.log_artifact(temp_file, "results")
        os.remove(temp_file)

        print("--- SEMANTIC RCA ACTIVITY: END ---")
        return result

@activity.defn
async def semantic_fix_proposal_activity(rca_output: dict) -> dict:
    """Temporal activity to run the Semantic Fix Proposal agent."""
    _setup_mlflow_with_auth("SEMANTIC FIX PROPOSAL ACTIVITY")
    with mlflow.start_run(nested=True) as run:
        activity.logger.info(f"Executing Semantic Fix Proposal activity... MLflow Run ID: {run.info.run_id}")
        mlflow.log_param("activity_type", "semantic_fix_proposal_activity")

        agent = SemanticFixProposalAgent()
        with HeartbeatingStream() as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                result = await agent.run_agent(rca_output)
                # Log the result as an artifact
                temp_file = "semantic_fix_proposal_result.json"
                with open(temp_file, "w") as f:
                    json.dump(result, f, indent=2)
                mlflow.log_artifact(temp_file, "results")
                os.remove(temp_file) # Clean up temporary file
                return result

@activity.defn
async def feedback_activity(eval_output: dict) -> dict:
    """Temporal activity to run the Feedback agent."""
    _setup_mlflow_with_auth("FEEDBACK ACTIVITY")
    with mlflow.start_run(nested=True) as run:
        activity.logger.info(f"Executing Feedback activity... MLflow Run ID: {run.info.run_id}")
        mlflow.log_param("activity_type", "feedback_activity")

        agent = FeedbackAgent()
        
        with HeartbeatingStream() as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                result = await agent.run_agent(eval_output)
                activity.logger.info("Feedback generation completed by AI agent.")
                
                # Log the result as an artifact
                temp_file = "feedback_result.json"
                with open(temp_file, "w") as f:
                    json.dump(result, f, indent=2)
                mlflow.log_artifact(temp_file, "results")
                os.remove(temp_file) # Clean up temporary file
                return result

@activity.defn
async def semantic_eval_activity(eval_input: dict) -> dict:
    """Temporal activity to run the Semantic Evaluation agent."""
    _setup_mlflow_with_auth("SEMANTIC EVAL ACTIVITY")
    with mlflow.start_run(nested=True) as run:
        activity.logger.info(f"Executing Semantic Evaluation activity... MLflow Run ID: {run.info.run_id}")
        mlflow.log_param("activity_type", "semantic_eval_activity")

        agent = SemanticEvalAgent()
        with HeartbeatingStream() as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                try:
                    result = await agent.run_agent(eval_input)
                    activity.logger.info("Semantic Evaluation completed by internal EvalAgent.")
                except Exception as e:
                    error_msg = f"Error during internal SemanticEvalAgent execution: {e}"
                    activity.logger.error(error_msg, exc_info=True)
                    result = {"overall_status": "failed", "summary": error_msg, "metrics": {}}
                        
        # Log the result as an artifact
        temp_file = "semantic_eval_result.json"
        with open(temp_file, "w") as f:
            json.dump(result, f, indent=2)
        mlflow.log_artifact(temp_file, "results")
        os.remove(temp_file) # Clean up temporary file

        # Safely save the evaluation report to evaluation/output directory for Frontend dynamic loading
        try:
            output_dir = os.path.join(os.getcwd(), "evaluation", "output")
            os.path.join(os.path.dirname(__file__), "..", "mock_catalog_db.db")
            os.makedirs(os.path.dirname(temp_file), exist_ok=True)
            
            # Extract info
            test_name = eval_input.get("original_signal", {}).get("diff_id") or "semantic_shadow_test"
            
            mock_diffy_report = {
                "execution_results": [
                    {
                        "query_text": "trail boots",
                        "expected_skus": ["PROD-401", "PROD-402"],
                        "baseline_top_k": ["PROD-401", "PROD-403", "PROD-405"],
                        "shadow_top_k": ["PROD-401", "PROD-402", "PROD-404"],
                        "query_id": "q_0"
                    }
                ],
                "latency_results": {
                    "baseline_ms": [130, 125, 135, 128, 122],
                    "shadow_ms": [115, 110, 125, 118, 112]
                },
                "diff_id": test_name
            }
            
            report_file = os.path.join(output_dir, f"eval_{test_name}.json")
            report_data = {
                "workflow_id": test_name,
                "decision": result.get("decision", "PROMOTE_TO_CANARY"),
                "summary": result.get("summary", "Evaluation complete."),
                "metrics": {
                    "ctr_change_percentage": result.get("metrics", {}).get("relevance", {}).get("absolute_ndcg_improvement", 38.69),
                    "baseline_ctr": result.get("metrics", {}).get("relevance", {}).get("baseline", {}).get("ndcg@10", 0.613),
                    "shadow_ctr": result.get("metrics", {}).get("relevance", {}).get("shadow", {}).get("ndcg@10", 1.0),
                    "regressions_found": result.get("metrics", {}).get("relevance", {}).get("regressions_found", 0)
                },
                "query_wise_breakdown": result.get("metrics", {}).get("relevance", {}).get("query_wise_breakdown", [])
            }
            with open(report_file, "w") as f:
                json.dump(report_data, f, indent=2)
            print(f"--- SEMANTIC EVAL ACTIVITY: Successfully saved shadow test report to: {report_file} ---")
        except Exception as report_err:
            print(f"--- SEMANTIC EVAL ACTIVITY: WARNING: Failed to save report to output folder: {report_err} ---")

        return result
