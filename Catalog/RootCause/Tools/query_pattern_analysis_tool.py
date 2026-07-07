from typing import Any, Dict, List
import re
from collections import Counter

class QueryPatternAnalysisTool:
    def __init__(self):
        pass

    def run(self, queries: List[str]) -> Dict[str, Any]:
        """
        Analyzes a list of problematic queries to identify common keywords, unusual patterns, or trends.
        """
        if not queries:
            return {"status": "success", "summary": "No queries provided for analysis."}

        all_keywords = []
        unusual_patterns = []
        
        for query in queries:
            # Basic keyword extraction
            words = re.findall(r'\b\w+\b', query.lower())
            all_keywords.extend(words)

            # Example: Detect queries that are unusually long or contain special characters
            if len(query) > 50 or re.search(r'[^\w\s]', query):
                unusual_patterns.append(query)

        keyword_counts = Counter(all_keywords)
        most_common_keywords = keyword_counts.most_common(5)

        summary = "Query pattern analysis completed."
        if most_common_keywords:
            summary += f" Most common keywords: {most_common_keywords}."
        if unusual_patterns:
            summary += f" Detected {len(unusual_patterns)} unusual query patterns."

        return {
            "status": "success",
            "summary": summary,
            "most_common_keywords": most_common_keywords,
            "unusual_queries": unusual_patterns,
        }