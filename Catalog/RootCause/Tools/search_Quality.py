import asyncio
import json
from dataclasses import dataclass, asdict
from typing import Any

from .catalog_repository import CatalogRepository
from .catalog_models import CatalogProduct
from .common_signals import sample_signal


@dataclass
class SearchQualityResult:
    tool_name: str
    status: str
    query: str
    total_products_checked: int
    relevant_products_found: int
    quality_score: float
    root_cause_candidate: str
    evidence: list[str]

class CatalogSearchQualityTool:
    def __init__(self, repository: CatalogRepository):
        self.repository = repository

    # async def run(self, signal_data: dict[str, 'Any']) -> list['SearchQualityResult']:
    #     if 'events' not in signal_data:
    #         return [SearchQualityResult(
    #             tool_name="CatalogSearchQualityTool",
    #             status="failed",
    #             query="",
    #             total_products_checked=0,
    #             relevant_products_found=0,
    #             quality_score=0.0,
    #             root_cause_candidate="missing_events_data",
    #             evidence=["'events' key not found in signal_data."],
    #         )]

    #     results = []
    #     for event in signal_data['events']:
    #         query_text = event.get("query", {}).get("text", "").strip().lower()

    #         if not query_text or event.get('response', {}).get('result_count', 0) == 0:
    #             continue

    #         products_data = event.get('response', {}).get('results', [])
    #         products = [CatalogProduct(product_id=p.get('product_id'), name="", description="", price=0.0, category="", in_stock=True) for p in products_data]

    #         if not products:
    #             continue

    #         total_products_checked = len(products)
    #         relevant_products_found = 0
    #         evidence: list[str] = []

    #         for product in products:
    #             if self._is_relevant(query_text, product):
    #                 relevant_products_found += 1
    #             else:
    #                 evidence.append(f"Product {product.product_id} is not directly relevant to query.")

    #         quality_score = (relevant_products_found / total_products_checked) * 100 if total_products_checked > 0 else 0.0
    #         status = "healthy" if quality_score > 50 else "degraded"
    #         root_cause_candidate = "none" if status == "healthy" else "low_search_relevance"

    #         results.append(SearchQualityResult(
    #             tool_name="CatalogSearchQualityTool",
    #             status=status,
    #             query=query_text,
    #             total_products_checked=total_products_checked,
    #             relevant_products_found=relevant_products_found,
    #             quality_score=round(quality_score, 2),
    #             root_cause_candidate=root_cause_candidate,
    #             evidence=evidence,
    #         ))
        
    #     return results
    
    # async def run(self, signal_data: dict[str, Any]) -> list[SearchQualityResult]:
    #     if 'events' not in signal_data:
    #         return [SearchQualityResult(
    #             tool_name="CatalogSearchQualityTool",
    #             status="failed",
    #             query="",
    #             total_products_checked=0,
    #             relevant_products_found=0,
    #             quality_score=0.0,
    #             root_cause_candidate="missing_events_data",
    #             evidence=["'events' key not found in signal_data."],
    #         )]

    #     results = []
    #     for event in signal_data['events']:
    #         query_text = event.get("query", {}).get("text", "").strip().lower()

    #         if not query_text or event.get('response', {}).get('result_count', 0) == 0:
    #             continue

    #         products_data = event.get('response', {}).get('results', [])
    #         products = [CatalogProduct(product_id=p.get('product_id'), name="", description="", price=0.0, category="", in_stock=True) for p in products_data]

    #         if not products:
    #             continue

    #         total_products_checked = len(products)
    #         relevant_products_found = 0
    #         evidence: list[str] = []

    #         for product in products:
    #             if self._is_relevant(query_text, product):
    #                 relevant_products_found += 1
    #             else:
    #                 evidence.append(f"Product {product.product_id} is not directly relevant to query.")

    #         quality_score = (relevant_products_found / total_products_checked) * 100 if total_products_checked > 0 else 0.0
    #         status = "healthy" if quality_score > 50 else "degraded"
    #         root_cause_candidate = "none" if status == "healthy" else "low_search_relevance"

    #         results.append(SearchQualityResult(
    #             tool_name="CatalogSearchQualityTool",
    #             status=status,
    #             query=query_text,
    #             total_products_checked=total_products_checked,
    #             relevant_products_found=relevant_products_found,
    #             quality_score=round(quality_score, 2),
    #             root_cause_candidate=root_cause_candidate,
    #             evidence=evidence,
    #         ))
        
    #     return results
    async def run(self, signal_data: dict[str, Any]) -> list[SearchQualityResult]:
        if 'events' not in signal_data:
            return [SearchQualityResult(
                tool_name="CatalogSearchQualityTool",
                status="failed",
                query="",
                total_products_checked=0,
                relevant_products_found=0,
                quality_score=0.0,
                root_cause_candidate="missing_events_data",
                evidence=["'events' key not found in signal_data."],
            )]

        results = []
        events = signal_data.get('events', [])

        for event in events:
            query_text = event.get("query", {}).get("text", "").strip().lower()
            response = event.get('response', {})

            # Skip events with no results, as relevance can't be judged.
            if not query_text or response.get('result_count', 0) == 0:
                continue

            # This tool's relevance check is simple. A real-world tool
            # would use embeddings, click models, or other signals.
            low_score_products = [
                p for p in response.get('results', [])
                if p.get('score', 1.0) < 0.5
            ]

            if low_score_products:
                quality_score = 100 - (len(low_score_products) / response.get('result_count')) * 100
                status = "degraded"
                root_cause_candidate = "low_search_relevance"
                evidence = [
                    f"Query '{query_text}' returned {len(low_score_products)} low-scoring products.",
                    f"Example low-score product: {low_score_products[0].get('product_id')} with score {low_score_products[0].get('score')}"
                ]
            else:
                quality_score = 100.0
                status = "healthy"
                root_cause_candidate = "none"
                evidence = [f"All products for query '{query_text}' have acceptable relevance scores."]

            results.append(SearchQualityResult(
                tool_name="CatalogSearchQualityTool",
                status=status,
                query=query_text,
                total_products_checked=response.get('result_count', 0),
                relevant_products_found=response.get('result_count', 0) - len(low_score_products),
                quality_score=round(quality_score, 2),
                root_cause_candidate=root_cause_candidate,
                evidence=evidence,
            ))

        if not results:
            return [SearchQualityResult(
                tool_name="CatalogSearchQualityTool",
                status="healthy",
                query="N/A",
                total_products_checked=len(events),
                relevant_products_found=len(events),
                quality_score=100.0,
                root_cause_candidate="none",
                evidence=["No events with low-scoring results found to analyze."],
            )]

        return results

    def _is_relevant(self, query: str, product: CatalogProduct) -> bool:
        # Simple keyword matching for relevance. In a real system, this would use embeddings.
        product_text = f"{product.brand} {product.category} {product.terrain_type} {product.status}".lower()
        return query in product_text


if __name__ == "__main__":
    async def main():
        repo = CatalogRepository()
        tool = CatalogSearchQualityTool(repo)

        # Example signal with a search query
        search_signal = {
            "catalog_entity": {
                "category": "Footwear",
                "brand": "Trailhead XT"
            },
            "search_query": "trail waterproof"
        }

        result = await tool.run(search_signal)

        print("\n")
        print("=" * 70)
        print("CATALOG SEARCH QUALITY RESULT")
        print("=" * 70)

        print(json.dumps(asdict(result), indent=2))

    asyncio.run(main())
