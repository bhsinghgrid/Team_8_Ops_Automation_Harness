from typing import Any, Dict, List

class ProductDataCompletenessTool:
    def __init__(self, repo):
        self.repo = repo # Assuming repo has a method to fetch product data

    def run(self, product_ids: List[str]) -> Dict[str, Any]:
        """
        Checks for completeness of critical product data fields for a given list of product IDs.
        Assumes the repo can fetch detailed product information.
        """
        missing_data = {}
        required_fields = ["title", "description", "category", "price", "image_url"]

        for product_id in product_ids:
            product_data = self.repo.get_product_data(product_id) # Placeholder for actual repo call
            
            if not product_data:
                missing_data[product_id] = {"status": "not_found", "details": "Product not found in repository."}
                continue

            missing_fields_for_product = []
            for field in required_fields:
                if field not in product_data or not product_data[field]:
                    missing_fields_for_product.append(field)
            
            if missing_fields_for_product:
                missing_data[product_id] = {
                    "status": "incomplete",
                    "details": f"Missing or empty fields: {', '.join(missing_fields_for_product)}"
                }
            else:
                missing_data[product_id] = {"status": "complete", "details": "All required fields present."}
        
        if not missing_data:
            return {"status": "success", "summary": "No product data completeness issues found."}
        
        return {"status": "issues_found", "summary": f"Found completeness issues for {len(missing_data)} products.", "details": missing_data}