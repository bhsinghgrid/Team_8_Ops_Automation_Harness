# temporal/workflows.py
"""
Temporal Workflows for the Magellan Runbook Execution Pipeline.
These workflows orchestrate the execution of AI-generated runbooks.
"""
from temporalio import workflow
from temporalio.exceptions import ActivityError
from datetime import timedelta

# Import ONLY schemas to keep the workflow deterministic and avoid circular imports
from temporal.schemas import OpsSignal, RootCauseReport, ImpactAnalysis, PreventionPlan, EvalReport, Runbook

@workflow.defn
class FullPipelineWorkflow:
    @workflow.run
    async def execute_full_pipeline(self, signal_data: dict) -> str:
        # Convert input dict to OpsSignal object
        signal = OpsSignal.model_validate(signal_data)
        
        workflow.logger.info(f"🚀 Starting Full Pipeline Workflow for signal: {signal.signal_id}")
        
        # Phase 1: AI Agent Pipeline to Generate Runbook
        # We manually validate activity results back into Pydantic models
        
        rc_data = await workflow.execute_activity("root_cause_activity", args=[signal], start_to_close_timeout=timedelta(minutes=5))
        root_cause_report = RootCauseReport.model_validate(rc_data)
        
        impact_data = await workflow.execute_activity("impact_activity", args=[signal, root_cause_report], start_to_close_timeout=timedelta(minutes=5))
        impact_report = ImpactAnalysis.model_validate(impact_data)
        
        prevention_data = await workflow.execute_activity("data_gap_activity", args=[signal, root_cause_report, impact_report], start_to_close_timeout=timedelta(minutes=5))
        prevention_plan = PreventionPlan.model_validate(prevention_data)
        
        eval_data = await workflow.execute_activity("eval_activity", args=[signal, root_cause_report], start_to_close_timeout=timedelta(minutes=10))
        eval_report = EvalReport.model_validate(eval_data)
        
        runbook_data = await workflow.execute_activity("fix_plan_activity", 
                                                 args=[signal, root_cause_report, impact_report, prevention_plan, eval_report], 
                                                 start_to_close_timeout=timedelta(minutes=5))
        runbook = Runbook.model_validate(runbook_data)
        
        workflow.logger.info(f"✅ Runbook {runbook.runbook_id} generated. Proceeding to execution phase.")

        # Phase 2: Runbook Execution (Governance, Deployment, Canary)
        await workflow.execute_activity("log_audit_activity", args=[runbook.runbook_id, "Workflow Started", "Runbook execution initiated."], start_to_close_timeout=timedelta(minutes=1))

        if runbook.approval_required:
            workflow.logger.info(f"🚨 Human approval required for runbook: {runbook.runbook_id}. Owner: {runbook.owner}")
            await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "PENDING_APPROVAL", f"Waiting for {runbook.owner} approval."], start_to_close_timeout=timedelta(minutes=1))
            await workflow.execute_activity("send_approval_request_activity", args=[runbook.runbook_id, runbook.owner, runbook.root_cause.root_cause, runbook.eval_report.eval_summary], start_to_close_timeout=timedelta(minutes=1))
            try:
                await workflow.execute_activity("wait_for_approval_signal_activity", args=[runbook.runbook_id, "Approved by Mock"], start_to_close_timeout=timedelta(minutes=10))
                workflow.logger.info(f"✅ Runbook {runbook.runbook_id} approved.")
                await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "APPROVED", "Runbook approved by human owner."], start_to_close_timeout=timedelta(minutes=1))
            except ActivityError as e:
                workflow.logger.error(f"❌ Runbook {runbook.runbook_id} approval failed: {e}")
                await workflow.execute_activity("trigger_rollback_activity", args=[runbook.runbook_id, "Approval Failed", str(e)], start_to_close_timeout=timedelta(minutes=1))
                await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "FAILED", str(e)], start_to_close_timeout=timedelta(minutes=1))
                return f"Workflow Failed: Runbook {runbook.runbook_id} was not approved."
        else:
            workflow.logger.info(f"🟢 No human approval required for runbook: {runbook.runbook_id}. Auto-executing.")
            await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "AUTO_APPROVED", "No approval needed; auto-executing."], start_to_close_timeout=timedelta(minutes=1))

        workflow.logger.info(f"🛠️ Executing fix steps for runbook: {runbook.runbook_id}")
        await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "IN_PROGRESS", "Applying immediate fix plan."], start_to_close_timeout=timedelta(minutes=1))
        try:
            await workflow.execute_activity("apply_fix_activity", args=[runbook.runbook_id, runbook.immediate_fix_plan], start_to_close_timeout=timedelta(minutes=10))
            workflow.logger.info(f"✅ Fix steps for {runbook.runbook_id} applied successfully.")
            await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "FIX_APPLIED", "Immediate fix plan applied."], start_to_close_timeout=timedelta(minutes=1))

            workflow.logger.info(f"📊 Starting canary monitoring for {runbook.runbook_id}...")
            await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "CANARY_MONITORING", "Initiating canary rollout."], start_to_close_timeout=timedelta(minutes=1))
            canary_status = await workflow.execute_activity("monitor_canary_activity", args=[runbook.runbook_id, runbook.eval_report.shadow_metrics], start_to_close_timeout=timedelta(minutes=10))
            
            if canary_status == "SUCCESS":
                workflow.logger.info(f"📈 Canary rollout for {runbook.runbook_id} successful.")
                await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "COMPLETED", "Canary successful; fix fully deployed."], start_to_close_timeout=timedelta(minutes=1))
                return f"Workflow Completed: Runbook {runbook.runbook_id} executed successfully."
            else:
                workflow.logger.warning(f"📉 Canary rollout for {runbook.runbook_id} failed: {canary_status}")
                await workflow.execute_activity("trigger_rollback_activity", args=[runbook.runbook_id, "Canary Failure", str(canary_status)], start_to_close_timeout=timedelta(minutes=1))
                await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "ROLLED_BACK", "Canary failed; rollback initiated."], start_to_close_timeout=timedelta(minutes=1))
                return f"Workflow Failed: Canary failure for {runbook.runbook_id}."
        except ActivityError as e:
            workflow.logger.error(f"❌ Error applying fix for {runbook.runbook_id}: {e}")
            await workflow.execute_activity("trigger_rollback_activity", args=[runbook.runbook_id, "Fix Application Failed", str(e)], start_to_close_timeout=timedelta(minutes=1))
            await workflow.execute_activity("update_runbook_status_activity", args=[runbook.runbook_id, "FAILED", str(e)], start_to_close_timeout=timedelta(minutes=1))
            return f"Workflow Failed: Fix application failed for {runbook.runbook_id}."

@workflow.defn
class SignalToRunbookWorkflow:
    @workflow.run
    async def execute(self, trigger_context: str = "Elasticsearch Ingestion") -> str:
        """
        This is the parent workflow. It orchestrates the entire process:
        1. Generates a signal from Elasticsearch.
        2. Starts the full AI agent pipeline as a child workflow.
        """
        workflow.logger.info(f"🚀 Starting parent workflow: {trigger_context}.")

        # Stage 1: Generate the signal from Elasticsearch
        signal_data = await workflow.execute_activity(
            "generate_signal_from_elasticsearch",
            start_to_close_timeout=timedelta(minutes=1),
        )
        # Identify the signal for the user
        signal_summary = signal_data.get("summary", "No summary found in signal_data")
        workflow.logger.info(f"✅ Fetched Signal: {signal_summary}")
        workflow.logger.info("Starting child workflow for runbook generation.")

        # Stage 2: Execute the runbook pipeline as a child workflow
        child_workflow_id = f"runbook-pipeline-for-signal"
        
        try:
            child_result = await workflow.execute_child_workflow(
                FullPipelineWorkflow.execute_full_pipeline,
                arg=signal_data,
                id=child_workflow_id,
                task_queue="magellan-runbook-execution-task-queue",
            )
            workflow.logger.info(f"✅ Child workflow finished with result: {child_result}")
            return f"Parent workflow completed. Child result: {child_result}"
        except ActivityError as e:
            workflow.logger.error(f"❌ Child workflow failed: {e}")
            return f"Parent workflow failed."
