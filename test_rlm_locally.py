# Runbook_System_Final/test_rlm_locally.py
"""
Mock runner to test RLM agents without requiring a live PostgreSQL database.
"""
import sys
from pathlib import Path
import time
import json

# Add paths
CURRENT_DIR = Path(__file__).resolve().parent
ROOT = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path: sys.path.insert(0, str(CURRENT_DIR))
if str(CURRENT_DIR / "agents") not in sys.path: sys.path.insert(0, str(CURRENT_DIR / "agents"))
if str(CURRENT_DIR / "brain") not in sys.path: sys.path.insert(0, str(CURRENT_DIR / "brain"))
if str(CURRENT_DIR / "shared") not in sys.path: sys.path.insert(0, str(CURRENT_DIR / "shared"))
if str(CURRENT_DIR / "tools") not in sys.path: sys.path.insert(0, str(CURRENT_DIR / "tools"))
if str(ROOT / "src") not in sys.path: sys.path.insert(0, str(ROOT / "src"))

from shared.schemas import OpsSignal, Runbook
from agents.root_cause import core as root_cause_agent
from agents.impact import core as impact_agent
from agents.data_gap import core as data_gap_agent
from agents.eval import core as eval_agent
from agents.fix_plan import core as fix_plan_agent

def execute_mock_pipeline(signal_file):
    with open(signal_file, 'r') as f:
        data = json.load(f)
    
    first_signal = data['signals'][0]
    ops_signal = OpsSignal(
        signal_id=first_signal['id'],
        signal_type=first_signal['type'],
        summary=first_signal['summary'],
        raw_data=first_signal
    )

    print("\n" + "="*60)
    print("🕵️  MOCK LOCAL TEST: MAGELLAN RLM TRACE")
    print("="*60)
    print(f"📡 SIGNAL: {ops_signal.signal_id} ({ops_signal.signal_type})")
    
    # RCA
    print("\n[1/5] RCA AGENT: Decomposing context...")
    rc_report = root_cause_agent.run(ops_signal)
    print(f"✅ Root Cause: {rc_report.root_cause}")
    print(f"✅ Capability: {rc_report.affected_capability}")

    # Impact
    print("\n[2/5] IMPACT AGENT: Assessing blast radius...")
    imp_report = impact_agent.run(rc_report)
    print(f"✅ Business Assessment: {imp_report.business_impact}")

    # Data Gap
    print("\n[3/5] DATA GAP AGENT: Auditing rules...")
    gap_report = data_gap_agent.run(rc_report, imp_report)
    print(f"✅ Recommended Test: {gap_report.missing_data_quality_tests[0]}")

    # Eval
    print("\n[4/5] EVAL AGENT: Running shadow replay...")
    e_report = eval_agent.run(ops_signal, rc_report)
    print(f"✅ Shadow Result: {e_report.assessment_state.upper()} (Conf: {e_report.confidence_score})")

    # Fix Plan
    print("\n[5/5] FIX PLAN AGENT: Enforcing Governance...")
    final = fix_plan_agent.run(ops_signal, rc_report, imp_report, gap_report, e_report)
    print(f"✅ Assigned Owner: {final.owner}")
    status = "🚨 GATED" if final.approval_required else "🟢 AUTO-CLOSE"
    print(f"✅ FINAL STATUS:  {status}")
    print("="*60)

if __name__ == "__main__":
    file = CURRENT_DIR / "samples" / "magellan_scenario_a_catalog.json"
    execute_mock_pipeline(str(file))
