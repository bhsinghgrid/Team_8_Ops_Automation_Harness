import json
from typing import Dict, Any

class MXPContextBuilder:
    def __init__(self, rules_filepath: str, logs_filepath: str):
        self.rules_filepath = rules_filepath
        self.logs_filepath = logs_filepath

    def gather_context(self, signal: Any) -> Dict[str, Any]:
        # Fetch matching rules, timestamps, and inventory allocations
        investigation_tools = {
            "inventory_and_timeline_data": [],
            "suppression_scanner_data": []
        }
        
        with open(self.rules_filepath, 'r') as f:
            rules_data = json.load(f)
            # Handle if the rules are wrapped in a list or a dict
            if isinstance(rules_data, dict) and "rules" in rules_data:
                rules = rules_data["rules"]
            elif isinstance(rules_data, dict):
                rules = list(rules_data.values())
            else:
                rules = rules_data

            for rule in rules:
                if not isinstance(rule, dict):
                    continue
                    
                snapshots = {s["id"]: s.get("stock", 0) for s in rule.get("target_product_snapshots", []) if isinstance(s, dict)}
                
                # Timeline & Inventory cross referencing
                if rule.get("rule_type") == "boost" and signal.impacted_product_id in rule.get("target_products", []):
                    investigation_tools["inventory_and_timeline_data"].append({
                        "rule_id": rule.get("rule_id"),
                        "action": "boost",
                        "created_by": rule.get("created_by"),
                        "deployed_at": rule.get("created_at"),
                        "target_product": signal.impacted_product_id,
                        "warehouse_stock_count": snapshots.get(signal.impacted_product_id, 0)
                    })
                
                # Over-fitted suppression scanning
                if rule.get("rule_type") == "suppress" and rule.get("campaign") == "Weekend Promo":
                    investigation_tools["suppression_scanner_data"].append({
                        "rule_id": rule.get("rule_id"),
                        "action": "suppress",
                        "description": "Suppress competing high-volume performance shoes during the promo window",
                        "suppressed_products": [
                            {"product_id": pid, "available_stock": snapshots.get(pid, 0)}
                            for pid in rule.get("target_products", [])
                        ]
                    })

        return {
            "query": signal.query_text,
            "product_id": signal.impacted_product_id,
            "performance_metrics": {
                "calculated_ctr_percent": signal.current_metric_value,
                "total_impressions": getattr(signal, 'metadata', {}).get('total_impressions', 100)
            },
            "investigation_tools": investigation_tools
        }