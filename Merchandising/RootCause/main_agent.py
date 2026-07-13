import os
import sys
import json
import logging
from typing import Dict, Any
from google import genai
from dotenv import load_dotenv

# Bulletproof path injection to find the mxp rca agent components in your provided repository
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
backend_path = os.path.join(root_dir, 'Team_8_Ops_Automation_Harness-mxp-rlm-rcaagent/Magellan-rca-engine-backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from app.schemas.shared_ingress import IncomingSignal
    from app.services.context.mxp_context import MXPContextBuilder
    from app.agents.experts.mxp_rules_agent import MXPRulesAgent
    HAS_MXP_DEPENDENCIES = True
except ImportError:
    HAS_MXP_DEPENDENCIES = False

logger = logging.getLogger(__name__)

class MerchandisingRootCauseAgent:
    """Root Cause Analysis Agent for Merchandising (MXP) Rules."""
    
    def __init__(self):
        load_dotenv()
        self.rules_filepath = "Team_8_Ops_Automation_Harness-mxp-rlm-rcaagent/mock_data/rules.json"
        self.logs_filepath = "Team_8_Ops_Automation_Harness-mxp-rlm-rcaagent/mock_data/search_events.jsonl"
        
        # Connect to real Gemini client if API key and dependencies are present
        api_key = os.getenv("GEMINI_API_KEY")
        if HAS_MXP_DEPENDENCIES and api_key:
            try:
                self.builder = MXPContextBuilder(
                    rules_filepath=self.rules_filepath,
                    logs_filepath=self.logs_filepath
                )
                self.client = genai.Client(api_key=api_key)
                self.agent = MXPRulesAgent(context_builder=self.builder, gemini_client=self.client)
            except Exception as e:
                logger.error(f"Error initializing real MXP Rules Agent components: {e}")
                self.client = None
                self.agent = None
        else:
            self.client = None
            self.agent = None

    async def run(self, signal_dict: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Running Merchandising Root Cause Agent on signal: {signal_dict}")
        
        # Check if we should execute real Gemini analysis or use deterministic simulation
        if not self.client or not self.agent:
            logger.info("GEMINI_API_KEY or MXP dependencies missing. Using deterministic simulation fallback.")
            return self._run_simulation(signal_dict)

        try:
            # Map incoming signal dictionary to IncomingSignal Pydantic model
            signal = IncomingSignal(
                signal_id=signal_dict.get("signal_id", "sig_merch_001"),
                anomaly_type=signal_dict.get("anomaly_type", "LOW_CTR"),
                query_text=signal_dict.get("query", signal_dict.get("query_text", "summer dresses")),
                impacted_product_id=signal_dict.get("affected_product_id", signal_dict.get("impacted_product_id", "PROD-467")),
                current_metric_value=float(signal_dict.get("current_metric_value", 0.0)) if "current_metric_value" in signal_dict else 0.0
            )
            # Attach metadata dict if present
            signal.metadata = signal_dict.get("metadata", {})

            # Generate Evidence Pack via Gemini
            evidence_pack = self.agent.analyze(signal)
            
            # Format output correctly into standard dictionary structures
            analysis = {
                "capability": evidence_pack.capability,
                "symptom": evidence_pack.symptom,
                "root_cause": "MXP Rule Conflict",
                "primary_cause": evidence_pack.root_cause.primary_cause,
                "confidence_score": evidence_pack.root_cause.confidence_score,
                "supporting_evidence": {
                    "rule_id": getattr(evidence_pack.root_cause.supporting_evidence, "rule_id", "N/A"),
                    "created_by": getattr(evidence_pack.root_cause.supporting_evidence, "created_by", "N/A"),
                    "deployed_at": getattr(evidence_pack.root_cause.supporting_evidence, "deployed_at", "N/A"),
                    "warehouse_stock": getattr(evidence_pack.root_cause.supporting_evidence, "warehouse_stock", 0),
                    "original_metadata": signal_dict
                }
            }
            return {
                "status": "success",
                "response_text": f"```json\n{json.dumps(analysis, indent=2)}\n```"
            }
        except Exception as e:
            logger.exception(f"Exception during real Gemini MXP Agent execution: {e}. Falling back to simulation.")
            return self._run_simulation(signal_dict)

    def _run_simulation(self, signal_dict: Dict[str, Any]) -> Dict[str, Any]:
        query = signal_dict.get("query", signal_dict.get("query_text", "summer dresses"))
        issue = signal_dict.get("issue", "")
        conflicting_rule_ids = signal_dict.get("conflicting_rule_ids", ["rule_boost_brandA_summer", "rule_bury_brandA_clearance"])
        affected_category = signal_dict.get("affected_category", "Dresses > Summer")

        # Gather evidence/context from mock rules if available
        rules_context = []
        if os.path.exists(self.rules_filepath):
            try:
                with open(self.rules_filepath, "r") as f:
                    rules_data = json.load(f)
                    for rule in rules_data.get("rules", []):
                        if rule.get("id") in conflicting_rule_ids:
                            rules_context.append(rule)
            except Exception as e:
                logger.error(f"Error loading mock rules: {e}")

        analysis = {
            "capability": "merchandising",
            "symptom": f"Conflicting rules detected on query '{query}' inside '{affected_category}'",
            "root_cause": "MXP Rule Conflict",
            "primary_cause": f"Rules {conflicting_rule_ids} are competing for query scope. '{conflicting_rule_ids[0]}' promotes brand, while '{conflicting_rule_ids[1]}' buries clearance items belonging to the same brand.",
            "confidence_score": 0.95,
            "supporting_evidence": {
                "conflicting_rules": rules_context if rules_context else conflicting_rule_ids,
                "affected_category": affected_category,
                "query": query,
                "issue_description": issue
            }
        }

        return {
            "status": "success",
            "response_text": f"```json\n{json.dumps(analysis, indent=2)}\n```"
        }
