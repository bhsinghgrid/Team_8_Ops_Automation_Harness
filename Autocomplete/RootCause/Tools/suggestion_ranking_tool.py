from typing import Any, Dict, List

class SuggestionRankingTool:
    def __init__(self):
        pass

    def run(self, query_suggestions: Dict[str, List[str]], expected_rankings: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Analyzes the ranking of autocomplete suggestions against expected rankings for given queries.
        query_suggestions: A dictionary where keys are queries and values are lists of suggested terms.
        expected_rankings: A dictionary where keys are queries and values are lists of ideally ranked suggested terms.
        """
        ranking_discrepancies = {}
        for query, suggestions in query_suggestions.items():
            expected = expected_rankings.get(query, [])
            if not expected:
                continue # Skip if no expected ranking is provided

            # Compare actual suggestions against expected ones
            issues = []
            for i, suggestion in enumerate(suggestions):
                if i < len(expected) and suggestion != expected[i]:
                    issues.append(f"Suggestion '{suggestion}' at rank {i+1} differs from expected '{expected[i]}'.")
                elif i >= len(expected) and suggestion in expected:
                    issues.append(f"Expected suggestion '{suggestion}' ranked lower than ideal.")
            
            if issues:
                ranking_discrepancies[query] = {"status": "discrepancy", "details": issues}
            else:
                ranking_discrepancies[query] = {"status": "aligned", "details": "Suggestions align with expected rankings."}
        
        if not ranking_discrepancies:
            return {"status": "success", "summary": "No ranking discrepancies found."}
        
        return {"status": "issues_found", "summary": f"Found ranking discrepancies for {len(ranking_discrepancies)} queries.", "details": ranking_discrepancies}