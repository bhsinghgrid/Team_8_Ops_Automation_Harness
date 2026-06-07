# temporal/governance/activities.py
"""
Governance-related Temporal Activities for approvals, auditing, and status updates.
"""

from temporalio.activity import activity_method
import asyncio
from typing import List, Dict, Any

@activity_method
async def send_approval_request_activity(runbook_id: str, owner: str, root_cause_summary: str, eval_summary: str) -> str:
    """
    Sends an approval request to the specified owner.
    """
    activity_info = activity_method.info()
    print(f"[Governance Activity] {activity_info.activity_type} for {runbook_id}: Sending approval request to {owner}...")
    print(f"  Reason: {root_cause_summary}")
    print(f"  Eval Summary: {eval_summary}")
    print(f"  (Mock: Approval link would be: http://temporal.example.com/approve/{runbook_id})")
    await asyncio.sleep(2)
    return "APPROVAL_REQUEST_SENT"

@activity_method
async def wait_for_approval_signal_activity(runbook_id: str, mock_approval_status: str) -> str:
    """
    (MOCK ACTIVITY) Waits for a human approval signal.
    """
    activity_info = activity_method.info()
    print(f"[Governance Activity] {activity_info.activity_type} for {runbook_id}: Waiting for human approval (Mocked: {mock_approval_status})...")
    await asyncio.sleep(3)
    print(f"[Governance Activity] {activity_info.activity_type} for {runbook_id}: Approval signal received.")
    return mock_approval_status

@activity_method
async def log_audit_activity(runbook_id: str, event: str, message: str) -> str:
    """
    Logs an audit event for the runbook's execution history.
    """
    activity_info = activity_method.info()
    print(f"[Governance Activity] {activity_info.activity_type} for {runbook_id}: {event} - {message}")
    return "AUDIT_LOGGED"

@activity_method
async def update_runbook_status_activity(runbook_id: str, status: str, message: str) -> str:
    """
    Updates the status of the runbook in an external system.
    """
    activity_info = activity_method.info()
    print(f"[Governance Activity] {activity_info.activity_type} for {runbook_id}: Status Update: {status} - {message}")
    return "STATUS_UPDATED"
