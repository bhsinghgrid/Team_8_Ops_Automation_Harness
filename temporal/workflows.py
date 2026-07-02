from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from temporal.activities import root_cause_activity, fix_proposal_activity, eval_activity, feedback_activity, release_activity
    from temporal.activities import autocomplete_root_cause_activity, autocomplete_fix_proposal_activity, autocomplete_eval_activity
    from temporal.activities import semantic_root_cause_activity, semantic_fix_proposal_activity, semantic_eval_activity


@workflow.defn
class UnifiedSearchAiRepairWorkflow:
    def __init__(self):
        self._is_approved = False

    @workflow.run
    async def run(self, signal: dict) -> dict:
        """
        Executes a unified pipeline that intelligently routes to the correct
        RCA and Fix agents based on the signal type, then uses a shared
        Eval and Release process with a human-in-the-loop approval step.
        """
        workflow.logger.info(f"Starting Unified Search AI Repair Workflow for signal type: {signal.get('type')}")

        signal_type = signal.get("type")
        if signal_type == "catalog":
            rca_activity = root_cause_activity
            fix_activity = fix_proposal_activity
            eval_activity_func = eval_activity
        elif signal_type == "autocomplete":
            rca_activity = autocomplete_root_cause_activity
            fix_activity = autocomplete_fix_proposal_activity
            eval_activity_func = autocomplete_eval_activity
        elif signal_type == "semantic":
            rca_activity = semantic_root_cause_activity
            fix_activity = semantic_fix_proposal_activity
            eval_activity_func = semantic_eval_activity
        else:
            raise ValueError(f"Unknown signal type: {signal_type}")

        rca_result = await workflow.execute_activity(
            rca_activity, signal, start_to_close_timeout=timedelta(minutes=10)
        )
        fix_result = await workflow.execute_activity(
            fix_activity, rca_result, start_to_close_timeout=timedelta(minutes=10)
        )

        # Create a combined input for the evaluation activity
        eval_input = {
            "fix_result": fix_result,
            "rca_result": rca_result,
            "original_signal": signal
        }
        eval_result = await workflow.execute_activity(
            eval_activity_func, eval_input, start_to_close_timeout=timedelta(minutes=5)
        )

        # Shared Human-in-the-loop and Release logic
        shadow_metrics = eval_result.get("metrics", {}).get("shadow") if isinstance(eval_result.get("metrics", {}).get("shadow"), dict) else {}
        ndcg_score = shadow_metrics.get("ndcg@10", 1.0)
        threshold = 0.84

        if ndcg_score < threshold:
            workflow.logger.warning(
                f"NDCG score of {ndcg_score} is below the threshold of {threshold}. "
                f"Workflow is paused pending human approval. To approve, run 'python3 -m temporal.signal_workflow.py'"
            )
            await workflow.wait_for(lambda: self._is_approved)
            workflow.logger.info("Deployment has been manually approved. Proceeding.")
        else:
            workflow.logger.info(
                f"NDCG score of {ndcg_score} is above threshold. Proceeding automatically."
            )
        
        approval_status = {
            "status": "Deployment Approved",
            "evaluation_summary": eval_result.get("summary", "N/A"),
            "final_ndcg": ndcg_score
        }

        # First run Canary Release / Deployment
        release_result = await workflow.execute_activity(
            release_activity, approval_status, start_to_close_timeout=timedelta(minutes=1)
        )

        # Then, run the Feedback agent AFTER the release to audit the results and provide final feedback
        feedback_input = {
            "overall_status": release_result.get("status", "success"),
            "decision": eval_result.get("decision", "PROMOTE_TO_CANARY"),
            "summary": eval_result.get("summary", ""),
            "release_details": release_result
        }
        feedback_result = await workflow.execute_activity(
            feedback_activity, feedback_input, start_to_close_timeout=timedelta(minutes=2)
        )

        workflow.logger.info("Unified Search AI Repair Workflow completed successfully.")
        return feedback_result

    @workflow.signal
    def approve_deployment(self):
        """Signal method to approve a deployment that is pending review."""
        self._is_approved = True

@workflow.defn
class SemanticAiRepairWorkflow:
    @workflow.run
    async def run(self, signal: dict) -> dict:
        """
        Executes the full Semantic Root Cause, Fix, and Evaluation pipeline.
        """
        workflow.logger.info("Starting Semantic AI Repair Workflow...")

        rca_result = await workflow.execute_activity(
            semantic_root_cause_activity, signal, start_to_close_timeout=timedelta(minutes=10)
        )
        fix_result = await workflow.execute_activity(
            semantic_fix_proposal_activity, rca_result, start_to_close_timeout=timedelta(minutes=10)
        )
        eval_result = await workflow.execute_activity(
            semantic_eval_activity, fix_result, start_to_close_timeout=timedelta(minutes=5)
        )
        
        approval_status = {
            "status": "Deployment Approved",
            "evaluation_summary": eval_result.get("summary", "N/A"),
            "final_ndcg": eval_result.get("metrics", {}).get("shadow", {}).get("ndcg@10", 1.0)
        }
        
        release_result = await workflow.execute_activity(
            release_activity, approval_status, start_to_close_timeout=timedelta(minutes=1)
        )
        
        feedback_input = {
            "overall_status": release_result.get("status", "success"),
            "decision": eval_result.get("decision", "PROMOTE_TO_CANARY"),
            "summary": eval_result.get("summary", ""),
            "release_details": release_result
        }
        feedback_result = await workflow.execute_activity(
            feedback_activity, feedback_input, start_to_close_timeout=timedelta(minutes=2)
        )
        
        workflow.logger.info("Semantic AI Repair Workflow completed successfully.")
        return feedback_result
