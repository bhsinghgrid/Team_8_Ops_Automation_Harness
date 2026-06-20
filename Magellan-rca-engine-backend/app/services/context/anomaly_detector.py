import json
from typing import List, Dict, Any

class AnomalyDetector:
    def __init__(self, logs_filepath: str, rules_filepath: str):
        self.logs_filepath = logs_filepath
        self.rules_filepath = rules_filepath

    def scan_for_anomalies(self) -> List[Dict[str, Any]]:
       # Step 1: Tool 1 & Tool 2 - Parse logs for CTR math per query-product pair
        stats = {}
        with open(self.logs_filepath, 'r') as f:
            for line in f:
                event = json.loads(line)
                query = event.get("query_text")
                
                # --- FIX: Extract string IDs from product results ---
                results = event.get("response", {}).get("results", [])
                for idx, res in enumerate(results):
                    # Safely handle if res is a dict or a plain string ID
                    product_id = res.get("id") if isinstance(res, dict) else res
                    
                    if not product_id:
                        continue
                        
                    key = (query, product_id) # Now a safe tuple of (str, str)
                    if key not in stats:
                        stats[key] = {"impressions": 0, "clicks": 0, "rank_1_count": 0}
                    stats[key]["impressions"] += 1
                    if idx == 0:  
                        stats[key]["rank_1_count"] += 1
                
                # --- FIX: Extract string IDs from clicks ---
                clicks = event.get("interaction", {}).get("clicks", [])
                for click in clicks:
                    product_id = click.get("id") if isinstance(click, dict) else click
                    
                    if not product_id:
                        continue
                        
                    key = (query, product_id)
                    if key in stats:
                        stats[key]["clicks"] += 1

        # Step 2: Extract Live Stock Snapshots and Suppression metadata from rules
        inventory_registry = {}
        active_rules = []
        with open(self.rules_filepath, 'r') as f:
            rules_data = json.load(f)
            
            # If your rules.json file is wrapped inside a dict key like {"rules": [...]}, extract it
            if isinstance(rules_data, dict) and "rules" in rules_data:
                rules_data = rules_data["rules"]
            elif isinstance(rules_data, dict):
                # If it's a flat dict containing rule configurations as keys, inspect the values
                rules_data = list(rules_data.values())

            for rule in rules_data:
                # CRITICAL DEFENSIVE CHECK: Skip if the item isn't a dictionary configuration
                if not isinstance(rule, dict):
                    continue
                    
                active_rules.append(rule)
                for snap in rule.get("target_product_snapshots", []):
                    if isinstance(snap, dict) and "id" in snap:
                        inventory_registry[snap["id"]] = snap.get("stock", 0)
        # Step 3: Combine metrics with business logic (Low Stock + Rank 1 + Bad CTR)
        anomalies = []
        anomaly_id = 1

        # Scan 1: Check log data for poor performance (Low CTR despite impressions)
        for (query, product_id), metrics in stats.items():
            ctr = (metrics["clicks"] / metrics["impressions"]) * 100 if metrics["impressions"] > 0 else 0
            current_stock = inventory_registry.get(product_id, 999) # Default to safe if not in rules

            # Adjusted threshold: Look for items with at least 2 impressions and 0% CTR, 
            # even if stock isn't critically low, as long as it's being boosted.
            if metrics["impressions"] >= 2 and ctr == 0:
                culprit_rule = "UNKNOWN"
                for rule in active_rules:
                    if rule.get("rule_type") == "boost" and product_id in rule.get("target_products", []):
                        culprit_rule = rule.get("rule_id", "UNKNOWN")
                        break
                
                # Only flag if there is a known rule affecting it, otherwise it's just normal bad performance
                if culprit_rule != "UNKNOWN":
                    anomalies.append({
                        "signal_id": f"SIG-MXP-{anomaly_id:03d}",
                        "anomaly_type": "POOR_PERFORMANCE",
                        "query_text": query,
                        "impacted_product_id": product_id,
                        "current_metric_value": ctr,
                        "metadata": {
                            "suspected_rule_id": culprit_rule,
                            "detected_stock": current_stock,
                            "total_impressions": metrics["impressions"]
                        }
                    })
                    anomaly_id += 1

        # Scan 2: Check rules directly for zero-stock boosts (The "Ghost Boost" anomaly)
        for rule in active_rules:
            if rule.get("rule_type") == "boost":
                for product_id in rule.get("target_products", []):
                    stock = inventory_registry.get(product_id, 999)
                    if stock == 0:
                        anomalies.append({
                            "signal_id": f"SIG-MXP-{anomaly_id:03d}",
                            "anomaly_type": "ZERO_STOCK_BOOST",
                            "query_text": "ALL_QUERIES (Rule Level Fault)",
                            "impacted_product_id": product_id,
                            "current_metric_value": 0.0,
                            "metadata": {
                                "suspected_rule_id": rule.get("rule_id"),
                                "detected_stock": 0,
                                "total_impressions": 0
                            }
                        })
                        anomaly_id += 1

        return anomalies