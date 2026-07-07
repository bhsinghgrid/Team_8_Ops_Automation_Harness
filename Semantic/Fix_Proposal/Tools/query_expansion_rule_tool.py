from typing import Any, Dict, List

class QueryExpansionRuleTool:
    def __init__(self, semantic_rule_service=None):
        self.semantic_rule_service = semantic_rule_service # Placeholder for a service managing semantic query rules

    def run(self, rule_name: str, query_patterns: List[str], expansion_terms: List[str], enabled: bool = True) -> Dict[str, Any]:
        """
        Adds or updates a query expansion rule for semantic search.
        rule_name: A unique name for the expansion rule.
        query_patterns: A list of query patterns that trigger this expansion.
        expansion_terms: A list of terms to expand the query with.
        enabled: Whether the rule should be enabled immediately.
        """
        if not self.semantic_rule_service:
            return {"status": "error", "summary": "Semantic rule service not configured."}
        if not rule_name or not query_patterns or not expansion_terms:
            return {"status": "error", "summary": "Invalid parameters for query expansion rule."}

        try:
            # Placeholder: In a real system, this would call an API to add/update query expansion rules.
            rule_status = self.semantic_rule_service.upsert_expansion_rule(rule_name, query_patterns, expansion_terms, enabled)
            
            if rule_status:
                return {
                    "status": "success",
                    "summary": f"Successfully {'updated' if rule_status == 'updated' else 'added'} query expansion rule '{rule_name}'.",
                    "details": {"rule_name": rule_name, "query_patterns": query_patterns, "expansion_terms": expansion_terms, "enabled": enabled}
                }
            else:
                return {
                    "status": "failed",
                    "summary": f"Failed to upsert query expansion rule '{rule_name}'.",
                    "details": "Service call failed or returned an error."
                }
        except Exception as e:
            return {
                "status": "error",
                "summary": f"An error occurred during upserting query expansion rule '{rule_name}'.",
                "details": str(e)
            }