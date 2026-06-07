# Runbook_System_Final/orchestration/orchestrator.py
"""Main orchestrator for the incident analysis runbook pipeline."""

import uuid
import time
import json
import asyncio
from shared.schemas import OpsSignal, Runbook, RunbookStatus
from orchestration.config import get_logger
from orchestration.database import RunbookDB
from orchestration import RLMClient # Import RLMClient from package namespace

# Import the core logic of each agent (now as classes)
from agents.root_cause.core import RootCauseAgent
from agents.impact.core import CapabilityImpactAgent
from agents.data_gap.core import DataGapAgent
from agents.eval.core import EvalAgent
from agents.fix_plan.core import FixPlanAgent

LOGGER = get_logger(__name__)
db = RunbookDB()

async def execute_pipeline(signal_data: dict) -> Runbook:
    """
    Runs the full agent pipeline from a raw signal to a final runbook.
    """
    print("\n" + "="*60)
    print("🚀 MAGELLAN AI SEARCH OPS: AGENT PIPELINE STARTED")
    print("="*60)

    rlm_client = RLMClient()

    first_signal_info = signal_data['signals'][0]
    ops_signal = OpsSignal(
        signal_id=first_signal_info['id'],
        signal_type=first_signal_info['type'],
        summary=first_signal_info['summary'],
        raw_data=first_signal_info
    )
    
    root_cause_agent = RootCauseAgent(rlm_client=rlm_client)
    impact_agent = CapabilityImpactAgent(rlm_client=rlm_client)
    data_gap_agent = DataGapAgent(rlm_client=rlm_client)
    eval_agent = EvalAgent(rlm_client=rlm_client)
    fix_plan_agent = FixPlanAgent(rlm_client=rlm_client)

    print(f"\n[0/6] 🗄️ DATABASE CHECK (Historical Knowledge)")
    print("-" * 60)
    print("  ...querying Runbook Registry for past incidents...")
    await asyncio.sleep(0.5)
    
    historical_data = db.get_historical_fix(ops_signal.signal_type, ops_signal.summary)
    
    if historical_data:
        print("  ⚡ HISTORICAL FIX FOUND! Bypassing AI Agents.")
        print(f"  ✅ Restoring Runbook: {historical_data['runbook_id']}")
        print(f"  ✅ Previous Owner:    {historical_data['owner']}")
        return Runbook.model_validate(historical_data)
        
    print("  ❌ No exact historical match found. Spinning up AI Agents...")
    await asyncio.sleep(0.5)

    print(f"\n[1/6] 📡 SIGNAL INGESTION")
    print("-" * 60)
    print(f"  • ID:      {ops_signal.signal_id}")
    print(f"  • Type:    {ops_signal.signal_type}")
    print(f"  • Summary: {ops_signal.summary}")
    await asyncio.sleep(0.5)

    print(f"\n[2/6] 🕵️ ROOT CAUSE AGENT (Diagnosis & Capability Mapping)")
    print("-" * 60)
    print("  ...analyzing raw telemetry and mapping capability...")
    await asyncio.sleep(1)
    root_cause_report = await root_cause_agent.run(ops_signal)
    print(f"  ✅ Capability Mapped: {root_cause_report.affected_capability}")
    print(f"  ✅ Root Cause Found:  {root_cause_report.root_cause}")
    print(f"  ✅ Evidence Stored:   {len(root_cause_report.evidence)} file(s) attached.")
    await asyncio.sleep(0.5)

    print(f"\n[3/6] 📊 CAPABILITY IMPACT AGENT (Business Assessment)")
    print("-" * 60)
    print("  ...evaluating blast radius and business risk...")
    await asyncio.sleep(1)
    impact_analysis = await impact_agent.run(ops_signal, root_cause_report)
    print(f"  ✅ Business Impact: {impact_analysis.business_impact}")
    if impact_analysis.affected_dashboards:
        print(f"  ✅ Dashboards Hit:  {', '.join(impact_analysis.affected_dashboards)}")
    await asyncio.sleep(0.5)

    print(f"\n[4/6] 🛡️ DATA GAP AGENT (Prevention & Rules)")
    print("-" * 60)
    print("  ...auditing tests and monitoring gaps...")
    await asyncio.sleep(1)
    prevention_plan = await data_gap_agent.run(ops_signal, root_cause_report, impact_analysis)
    print(f"  ✅ Missing QA Tests: {len(prevention_plan.missing_data_quality_tests)} identified.")
    
    print(f"\n[5/6] ⚖️ EVAL FACTORY (Shadow Testing)")
    print("-" * 60)
    print("  ...running diffy shadow comparison against candidate fix...")
    await asyncio.sleep(1)
    eval_report = await eval_agent.run(ops_signal, root_cause_report)
    print(f"  ✅ Shadow Status: {eval_report.assessment_state.upper()}")
    print(f"  ✅ Confidence:    {eval_report.confidence_score:.2f}")

    print(f"\n[6/6] 🛠️ FIX PLAN AGENT (Governance & Resolution)")
    print("-" * 60)
    print("  ...applying g(a,E,Pi) safety gating equation and drafting runbook...")
    await asyncio.sleep(1)
    final_runbook = await fix_plan_agent.run(
        signal=ops_signal,
        root_cause=root_cause_report,
        impact=impact_analysis,
        prevention=prevention_plan,
        eval_report=eval_report
    )
    
    print(f"  ✅ Assigned Owner: {final_runbook.owner}")
    
    if final_runbook.approval_required:
        print(f"  🚨 HUMAN APPROVAL: REQUIRED (High-Risk/Tier 2+ Block)")
    else:
        print(f"  🟢 HUMAN APPROVAL: BYPASSED (Low-Risk/Auto-Close Allowed)")
        
    print("  ✅ Fix Plan Steps:")
    for step in final_runbook.immediate_fix_plan:
        print(f"      - {step}")
    
    await asyncio.sleep(0.5)
    
    print("\n[💾] RUNBOOK REGISTRY UPDATE")
    print("-" * 60)
    print("  ...saving verified runbook to persistent storage...")
    final_runbook.status = RunbookStatus.COMPLETED # Set status before saving
    db.save_runbook(final_runbook)
    print("  ✅ Save complete.")
    
    print("\n" + "="*60)
    print(f"🎉 RUNBOOK GENERATED SUCCESSFULLY: {final_runbook.runbook_id}")
    print("="*60)
    
    return final_runbook

async def run_from_file(filepath: str) -> Runbook:
    """Helper to run the pipeline from a JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return await execute_pipeline(data)
