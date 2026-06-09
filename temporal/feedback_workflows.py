# temporal/feedback_workflows.py
from temporalio import workflow
from temporalio.exceptions import ActivityError
from datetime import timedelta
from typing import Dict, Any

# Import schemas
from temporal.schemas import OpsSignal, RootCauseReport, ImpactAnalysis, PreventionPlan, EvalReport, Runbook

@workflow.defn
class IntegratedFeedbackWorkflow:
    @workflow.run
    async def execute(self, signal_data: dict) -> str:
        # Convert input dict to OpsSignal object
        signal = OpsSignal.model_validate(signal_data)
        
        workflow.logger.info(f"🚀 Starting Integrated Feedback Workflow for signal: {signal.signal_id}")
        
        # Phase 1: AI Agent Pipeline (Reusing existing activities from all_activities)
        rc_data = await workflow.execute_activity("root_cause_activity", args=[signal], start_to_close_timeout=timedelta(minutes=5))
        root_cause_report = RootCauseReport.model_validate(rc_data)
        
        impact_data = await workflow.execute_activity("impact_activity", args=[signal, root_cause_report], start_to_close_timeout=timedelta(minutes=5))
        impact_report = ImpactAnalysis.model_validate(impact_data)
        
        prevention_data = await workflow.execute_activity("data_gap_activity", args=[signal, root_cause_report, impact_report], start_to_close_timeout=timedelta(minutes=5))
        prevention_plan = PreventionPlan.model_validate(prevention_data)
        
        eval_data = await workflow.execute_activity("eval_activity", args=[signal, root_cause_report], start_to_close_timeout=timedelta(minutes=10))
        eval_report = EvalReport.model_validate(eval_data)

        # New step: Suggest Tuning
        tuning_pack = await workflow.execute_activity(
            "suggest_tuning_activity", 
            args=[signal, root_cause_report, impact_report], 
            start_to_close_timeout=timedelta(minutes=5)
        )
        workflow.logger.info(f"✨ Suggest Tuning Pack generated: {len(tuning_pack.get('suggest_service_pack', {}).get('candidates', []))} candidates found.")
        
        runbook_data = await workflow.execute_activity("fix_plan_activity", 
                                                 args=[signal, root_cause_report, impact_report, prevention_plan, eval_report], 
                                                 start_to_close_timeout=timedelta(minutes=5))
        runbook = Runbook.model_validate(runbook_data)
        
        workflow.logger.info(f"✅ Runbook {runbook.runbook_id} generated.")

        # Phase 2: Execution & Feedback
        if runbook.approval_required:
            workflow.logger.info(f"🚨 Approval required for {runbook.runbook_id}")
            # Mocking approval for this demonstration
            await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "APPROVED", "Auto-approved for integration check."], start_to_close_timeout=timedelta(minutes=1))
        
        # Apply the fix first
        workflow.logger.info(f"🛠️ Applying fix for {runbook.runbook_id}...")
        apply_status = await workflow.execute_activity(
            "apply_fix_activity", 
            args=[runbook.runbook_id, runbook.immediate_fix_plan], 
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Run the new Feedback Agent activity
        workflow.logger.info(f"🔄 Running Feedback Agent for {runbook.runbook_id}...")
        from temporal.feedback_activities import run_feedback_agent_activity, run_canary_rollout_activity
        
        feedback_result = await workflow.execute_activity(
            run_feedback_agent_activity, 
            args=[runbook_data, apply_status], 
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        if feedback_result.get("status") == "ok" or feedback_result.get("status") == "degraded":
            workflow.logger.info(f"✅ Feedback Agent passed. Proceeding to Canary Rollout.")
            
            # Run the new Canary Rollout activity
            canary_status = await workflow.execute_activity(
                run_canary_rollout_activity, 
                args=[runbook_data, apply_status], 
                start_to_close_timeout=timedelta(minutes=15)
            )
            
            if canary_status == "COMPLETED":
                await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "COMPLETED", "Canary successful via Feedback layer."], start_to_close_timeout=timedelta(minutes=1))
                return f"Workflow Completed: Runbook {runbook.runbook_id} promoted to 100%."
            else:
                await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "ROLLED_BACK", f"Canary failed: {canary_status}"], start_to_close_timeout=timedelta(minutes=1))
                return f"Workflow Failed: Canary status {canary_status}."
        else:
            workflow.logger.error(f"❌ Feedback Agent failed: {feedback_result.get('message')}")
            return f"Workflow Failed: Feedback Agent reported error."

@workflow.defn
class IntegratedSignalToRunbookWorkflow:
    @workflow.run
    async def execute(self, trigger_context: str = "Feedback Integration Check") -> str:
        workflow.logger.info(f"🚀 Starting parent workflow: {trigger_context}")
        
        # In a real scenario, this would generate a signal and then call IntegratedFeedbackWorkflow
        # For now, let's just trigger a child workflow with a mock signal
        mock_signal = {
            "signal_id": "sig-feedback-test",
            "signal_type": "zero_result_query",
            "summary": "High zero-result rate for 'hybrid work backpack'",
            "severity": "high",
            "raw_data": {"query": "hybrid work backpack"}
        }
        
        return await workflow.execute_child_workflow(
            IntegratedFeedbackWorkflow.execute,
            args=[mock_signal],
            id="integrated-feedback-child-workflow"
        )
