from typing import Any, Dict, List
import re
from collections import Counter

class DataReconciliationTool:
    def __init__(self, repository):
        self.repository = repository # Assuming repository can fetch and compare data from multiple sources

    def run(self, product_ids: List[str], source_priority: List[str]) -> Dict[str, Any]:
        """
        Reconciles conflicting data for a list of product IDs by fetching from multiple sources
        and applying updates based on a defined source_priority.
        Example: product_ids=["PROD-123"], source_priority=["master_data_system", "ecommerce_feed"]
        """
        reconciliation_results = {}
        for product_id in product_ids:
            try:
                reconciled_data = self.repository.reconcile_product_data(product_id, source_priority)
                if reconciled_data:
                    reconciliation_results[product_id] = {
                        "status": "reconciled",
                        "summary": f"Successfully reconciled data for product {product_id}.",
                        "new_data": reconciled_data
                    }
                else:
                    reconciliation_results[product_id] = {
                        "status": "failed",
                        "summary": f"Could not reconcile data for product {product_id}.",
                        "details": "No data found or reconciliation logic failed."
                    }
            except Exception as e:
                reconciliation_results[product_id] = {
                    "status": "error",
                    "summary": f"An error occurred during reconciliation for product {product_id}.",
                    "details": {"error": str(e)}
                }
        
        if not reconciliation_results:
            return {"status": "success", "summary": "No product IDs provided for reconciliation."}

        return {"status": "completed", "summary": "Data reconciliation process finished.", "results": reconciliation_results}