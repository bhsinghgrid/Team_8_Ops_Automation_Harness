"""
Catalog Coverage Tool

Purpose:
--------
Detect catalog coverage issues for the SearchOps Root Cause Agent:
  - Missing required product attributes
  - Empty catalog slices (no products for brand/category)
  - Stale catalog data (last update beyond threshold)

Architecture:
-------------
CatalogCoverageTool -> CatalogRepositoryProtocol -> mock / DB / API

The tool never imports mock_catalog_db directly; all data access flows
through the injected repository so backend swaps require no tool changes.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Set

from .catalog_repository import CatalogRepository, CatalogRepositoryProtocol
from .catalog_models import CatalogProduct


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

STALE_THRESHOLD_HOURS: int = 24

REQUIRED_ATTRIBUTES: List[str] = [
    "product_id",
    "name",
    "description",
    "price",
    "category",
    "in_stock",
]


@dataclass
class CatalogCoverageResult:
    """Structured output returned to the Root Cause Agent."""

    status: str
    coverage_score: float
    total_products: int
    active_products: int
    affected_products: int
    missing_attributes: List[str]
    db_stale: bool
    last_update: Optional[str]
    root_cause_candidate: str
    evidence: List[str]


class CatalogCoverageTool:
    """
    Analyzes catalog coverage for a brand/category slice.

    Accepts an optional repository for dependency injection during tests or
    when pointing at PostgreSQL, MongoDB, Atlan, or a catalog service.
    """

    def __init__(
        self,
        repository: Optional[CatalogRepositoryProtocol] = None,
    ) -> None:
        self._repository: CatalogRepositoryProtocol = (
            repository if repository is not None else CatalogRepository()
        )

    # async def run(self, signal_data: dict[str, 'Any']) -> 'CatalogCoverageResult':
    #     """
    #     Execute coverage analysis for the catalog entity in signal_data.
    #     """
    #     products = []
    #     last_update = None
    #     evidence: List[str] = []
    #     missing_attributes: Set[str] = set()
    #     root_cause_candidate = "none"

    #     if 'events' in signal_data:
    #         events = signal_data['events']
    #         for event in events:
    #             if event.get('response', {}).get('result_count', 0) == 0:
    #                 evidence.append(f"Found zero-result query: {event.get('query', {}).get('text')}")

    #         if evidence:
    #             root_cause_candidate = "catalog_coverage_issue"

    #     if 'catalog_data' in signal_data:
    #         try:
    #             # Use a single product from the catalog_data for analysis
    #             product_data = json.loads(signal_data['catalog_data'])
    #             products = [CatalogProduct(**product_data)]
    #         except (json.JSONDecodeError, TypeError):
    #             return CatalogCoverageResult(
    #                 status="degraded",
    #                 coverage_score=0.0,
    #                 total_products=0,
    #                 active_products=0,
    #                 affected_products=0,
    #                 missing_attributes=[],
    #                 db_stale=False,
    #                 last_update=None,
    #                 root_cause_candidate="malformed_json",
    #                 evidence=["Input data is not valid JSON."],
    #             )
    #     else:
    #         catalog_entity = signal_data.get("catalog_entity", {})
    #         brand = str(catalog_entity.get("brand", "")).strip()
    #         category = str(catalog_entity.get("category", "")).strip()
    #         products = await self._repository.get_products(brand=brand, category=category)
    #         last_update = await self._repository.get_last_update_time(brand=brand, category=category)

    #     if not products:
    #         return CatalogCoverageResult(
    #             status="degraded",
    #             coverage_score=0.0,
    #             total_products=0,
    #             active_products=0,
    #             affected_products=0,
    #             missing_attributes=[],
    #             db_stale=False,
    #             last_update=None,
    #             root_cause_candidate="catalog_coverage_gap",
    #             evidence=["No catalog products found."],
    #         )

    #     total_products = len(products)
    #     active_products = sum(1 for product in products if product.in_stock)

    #     total_products = len(products)
    #     active_products = sum(1 for product in products if product.status == "active")
    #     affected_products = 0
    #     for product in products:
    #         product_missing = self._get_missing_attributes(product)
    #         if product_missing:
    #             affected_products += 1
    #             missing_attributes.update(product_missing)

    #     sorted_missing = sorted(missing_attributes)
    #     coverage_score = round(((total_products - affected_products) / total_products) * 100, 2)
    #     db_stale = self._is_catalog_stale(last_update)

    #     if db_stale:
    #         root_cause_candidate = "stale_catalog_data"
    #     if affected_products > 0 and root_cause_candidate == "none":
    #         root_cause_candidate = "catalog_attribute_gap"
        
    #     if db_stale:
    #         evidence.append("Catalog data is stale")
    #     if affected_products > 0:
    #         noun = "product" if affected_products == 1 else "products"
    #         evidence.append(f"{affected_products} {noun} missing required attributes")
    #     for attribute in sorted_missing:
    #         evidence.append(f"Missing attribute: {attribute}")

    #     status = self._resolve_status(affected_products=affected_products, db_stale=db_stale)

    #     return CatalogCoverageResult(
    #         status=status,
    #         coverage_score=coverage_score,
    #         total_products=total_products,
    #         active_products=active_products,
    #         affected_products=affected_products,
    #         missing_attributes=sorted_missing,
    #         db_stale=db_stale,
    #         last_update=last_update,
    #         root_cause_candidate=root_cause_candidate,
    #         evidence=evidence,
    #     )

    async def run(self, signal_data: dict[str, Any]) -> CatalogCoverageResult:
        """
        Execute coverage analysis on a batch of search events.
        """
        if 'events' not in signal_data or not isinstance(signal_data['events'], list):
            return CatalogCoverageResult(
                status="failed",
                coverage_score=0.0,
                total_products=0,
                active_products=0,
                affected_products=0,
                missing_attributes=[],
                db_stale=False,
                last_update=None,
                root_cause_candidate="missing_event_data",
                evidence=["Could not find the 'events' JSON object in the context."],
            )

        events = signal_data['events']
        total_events = len(events)
        zero_result_searches = 0
        evidence = []
        
        for event in events:
            if event.get('response', {}).get('result_count', -1) == 0:
                zero_result_searches += 1
                query_text = event.get('query', {}).get('text', 'N/A')
                evidence.append(f"Zero-result search for query: '{query_text}'")

        coverage_score = ((total_events - zero_result_searches) / total_events) * 100 if total_events > 0 else 100.0
        status = "degraded" if zero_result_searches > 0 else "healthy"
        root_cause_candidate = "catalog_coverage_issue" if zero_result_searches > 0 else "none"

        return CatalogCoverageResult(
            status=status,
            coverage_score=round(coverage_score, 2),
            total_products=total_events,  # Using total events as a proxy for total products
            active_products=total_events - zero_result_searches,
            affected_products=zero_result_searches,
            missing_attributes=[],
            db_stale=False,
            last_update=None,
            root_cause_candidate=root_cause_candidate,
            evidence=evidence,
        )

    @staticmethod
    def _get_missing_attributes(product: CatalogProduct) -> list[str]:
        """
        Return required attribute names that are absent on a single product.

        A value is considered missing when it is None or an empty string.
        """

        missing: List[str] = []
        for attribute in REQUIRED_ATTRIBUTES:
            value = getattr(product, attribute, None)
            if value is None or value == "":
                missing.append(attribute)
        return missing

    @staticmethod
    def _parse_utc_timestamp(timestamp: str) -> datetime:
        """Parse ISO-8601 UTC timestamps, including trailing 'Z'."""

        normalized = timestamp.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)

    def _is_catalog_stale(self, last_update: Optional[str]) -> bool:
        """
        Compare current UTC time against the latest catalog update.

        Returns True when last_update is older than STALE_THRESHOLD_HOURS.
        """

        if last_update is None:
            return False

        last_update_dt = self._parse_utc_timestamp(last_update)
        now_utc = datetime.now(timezone.utc)
        age_hours = (now_utc - last_update_dt).total_seconds() / 3600
        return age_hours > STALE_THRESHOLD_HOURS

    @staticmethod
    def _resolve_status(
        affected_products: int,
        db_stale: bool,
    ) -> str:
        """
        Map detected issues to an overall health status.

        healthy  -> no stale data and no attribute gaps
        degraded -> stale data and/or products missing required attributes
        """

        if db_stale or affected_products > 0:
            return "degraded"
        return "healthy"


# ---------------------------------------------------------------------------
# Local testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from Catalog.RootCause.Tools.common_signals import sample_signal


    async def main() -> None:
        tool = CatalogCoverageTool()
        result = await tool.run(sample_signal)

        print()
        print("=" * 60)
        print("CATALOG COVERAGE RESULT")
        print("=" * 60)
        print(json.dumps(asdict(result), indent=2))

    asyncio.run(main())
