import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.observation import OpsEvent, ZeroResultCluster
from app.providers.base import MalformedProviderResponse
from app.providers.ocs_catalog import OCSCatalogClient
from app.providers.product_state_manager import ProductStateManager
from app.providers.rule_state_manager import RuleStateManager
from app.schemas.signal_schema import (
    BatchSearchRequest,
    CatalogDiffRequest,
    CatalogDeltaRequest,
    RuleDiffRequest,
    SearchSignalRequest,
)
from app.services.search_provider_factory import get_search_provider
from app.utils.diff_utils import detect_missing_attributes
from app.utils.severity import determine_catalog_severity, determine_rule_severity

logger = logging.getLogger(__name__)

STOPWORDS = {"a", "the", "for", "with"}


class CatalogSyncError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_query_intent(query_text: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", query_text.lower())
    return " ".join(token for token in tokens if token not in STOPWORDS)


def is_missing_catalog_value(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def normalize_search_filters(filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not filters:
        return {}
    normalized = {}
    for key, value in filters.items():
        if key == "additionalProp1":
            continue
        if value is None or value == "" or value == [] or value == {}:
            continue
        normalized[key] = value
    return normalized


def normalize_search_sort(sort: Optional[str]) -> Optional[str]:
    if sort is None:
        return None
    normalized = sort.strip()
    if not normalized or normalized == "string":
        return None
    return normalized


def catalog_delta_severity(signal: CatalogDeltaRequest) -> str:
    missing_attributes = signal.missing_attributes
    if signal.operation.upper() == "INSERT" and not missing_attributes:
        missing_attributes = detect_missing_attributes(signal.after)
    request = CatalogDiffRequest(
        product_id=signal.product_id,
        operation=signal.operation,
        changed_fields=signal.changed_fields,
        before=signal.before or None,
        after=signal.after or None,
        missing_attributes=missing_attributes,
    )
    return determine_catalog_severity(request)


def targets_out_of_stock_product(value: Any) -> bool:
    if isinstance(value, dict):
        stock = value.get("stock")
        inventory_status = value.get("inventory_status")
        if stock == 0 or str(inventory_status).lower() == "out_of_stock":
            return True
        return any(targets_out_of_stock_product(child) for child in value.values())

    if isinstance(value, list):
        return any(targets_out_of_stock_product(item) for item in value)

    return False


def rule_diff_severity(signal: RuleDiffRequest) -> str:
    return determine_rule_severity(signal)


class IngestionService:

    def __init__(
        self,
        provider=None,
        now_fn: Callable[[], datetime] = utc_now,
        product_state_manager: Optional[ProductStateManager] = None,
        catalog_client: Optional[OCSCatalogClient] = None,
        rule_state_manager: Optional[RuleStateManager] = None,
    ):
        self.provider = provider
        self.now_fn = now_fn
        self.product_state_manager = product_state_manager
        self.catalog_client = catalog_client
        self.rule_state_manager = rule_state_manager

    async def ingest_query(
        self,
        db: Session,
        query_id: Optional[str],
        query_text: str,
        tenant: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Tuple[Optional[OpsEvent], bool]:
        request = SearchSignalRequest(
            query_id=query_id,
            query_text=query_text,
            tenant=tenant,
            limit=limit,
            offset=offset,
            filters=filters or {},
            sort=sort,
        )
        return await self.ingest_search(db, request)

    async def ingest_search(self, db: Session, signal: SearchSignalRequest) -> Tuple[Optional[OpsEvent], bool]:
        provider = self.provider or get_search_provider()
        tenant = signal.tenant or settings.OCS_TENANT
        timestamp = self.now_fn()
        filters = normalize_search_filters(signal.filters)
        sort = normalize_search_sort(signal.sort)

        try:
            provider_result = await provider.search(
                query_text=signal.query_text,
                tenant=tenant,
                limit=signal.limit,
                offset=signal.offset,
                filters=filters,
                sort=sort,
            )
        except MalformedProviderResponse:
            logger.exception("Skipping malformed provider response for query %s", signal.query_text)
            return None, False

        provider_result["tenant"] = provider_result.get("tenant") or tenant
        provider_result["query_id"] = signal.query_id
        provider_result["query_text"] = signal.query_text
        provider_result["limit"] = signal.limit
        provider_result["offset"] = signal.offset
        provider_result["filters"] = filters
        if sort:
            provider_result["sort"] = sort

        severity = self._search_result_severity(provider_result)
        event = OpsEvent(
            event_id=self._search_event_id(tenant, signal.query_text, timestamp),
            event_type="search_result",
            source_capability="semantic_search",
            severity=severity,
            timestamp=timestamp,
            provider="ocs" if provider_result.get("provider") == "ocs" else str(provider_result.get("provider") or "manual"),
            tenant=tenant,
            payload=provider_result,
        )
        persisted_event, created = self._insert_event_ignore_duplicate(db, event)

        if created and provider_result.get("success") and int(provider_result.get("result_count") or 0) == 0:
            self.upsert_zero_result_cluster(db, signal.query_text, timestamp)

        return persisted_event, created

    async def ingest_search_batch(self, db: Session, batch: BatchSearchRequest) -> Dict[str, Any]:
        queries = self._load_batch_queries(batch.queries_file)
        event_ids: List[str] = []
        errors: List[Dict[str, Any]] = []
        succeeded = 0
        failed = 0
        zero_result_count = 0

        for query in queries:
            query_id = query.get("query_id")
            query_text = query.get("query_text")
            if not query_text:
                failed += 1
                errors.append({"query_id": query_id, "error": "missing_query_text"})
                continue

            try:
                event, created = await self.ingest_query(
                    db=db,
                    query_id=query_id,
                    query_text=query_text,
                    tenant=batch.tenant,
                    limit=batch.limit,
                    offset=batch.offset,
                )
            except Exception as exc:
                logger.exception("Batch query ingestion failed for %s", query_id or query_text)
                failed += 1
                errors.append({"query_id": query_id, "query_text": query_text, "error": str(exc)})
                continue

            if event is None:
                failed += 1
                errors.append({"query_id": query_id, "query_text": query_text, "error": "malformed_response"})
                continue

            succeeded += 1
            event_ids.append(event.event_id)
            if created and event.payload.get("success") and int(event.payload.get("result_count") or 0) == 0:
                zero_result_count += 1

        return {
            "total": len(queries),
            "succeeded": succeeded,
            "failed": failed,
            "zero_result_count": zero_result_count,
            "event_ids": event_ids,
            "errors": errors,
        }

    def ingest_catalog_delta(self, db: Session, signal: CatalogDeltaRequest) -> Tuple[OpsEvent, bool]:
        missing_attributes = signal.missing_attributes
        if signal.operation.upper() == "INSERT" and not missing_attributes:
            missing_attributes = detect_missing_attributes(signal.after)
        request = CatalogDiffRequest(
            product_id=signal.product_id,
            operation=signal.operation,
            changed_fields=signal.changed_fields,
            before=signal.before or None,
            after=signal.after or None,
            missing_attributes=missing_attributes,
        )
        return self.ingest_catalog_diff(db, request)

    def ingest_catalog_diff(self, db: Session, signal: CatalogDiffRequest) -> Tuple[OpsEvent, bool]:
        timestamp = self.now_fn()
        payload = signal.model_dump()

        event = OpsEvent(
            event_id=self._uuid_event_id("CAT", timestamp),
            event_type="catalog_delta",
            source_capability="catalog",
            severity=determine_catalog_severity(signal),
            timestamp=timestamp,
            provider="manual",
            tenant=settings.OCS_TENANT,
            payload=payload,
        )
        persisted_event, created = self._insert_event_ignore_duplicate(db, event)
        if created and self.product_state_manager is not None:
            product = self.product_state_manager.apply_diff(signal)
            if self.catalog_client is not None:
                self._sync_catalog_diff_to_ocs(signal, product)
        return persisted_event, created

    def ingest_rule_diff(self, db: Session, signal: RuleDiffRequest) -> Tuple[OpsEvent, bool]:
        timestamp = self.now_fn()
        payload = signal.model_dump()

        event = OpsEvent(
            event_id=self._uuid_event_id("MXP", timestamp),
            event_type="rule_diff",
            source_capability="mxp_merchandising",
            severity=determine_rule_severity(signal),
            timestamp=timestamp,
            provider="manual",
            tenant=settings.OCS_TENANT,
            payload=payload,
        )
        persisted_event, created = self._insert_event_ignore_duplicate(db, event)
        if created and self.rule_state_manager is not None:
            self.rule_state_manager.apply_diff(signal)
        return persisted_event, created

    def list_events(
        self,
        db: Session,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        zero_results_only: bool = False,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[OpsEvent]:
        query = db.query(OpsEvent)
        if event_type:
            query = query.filter(OpsEvent.event_type == event_type)
        if severity:
            query = query.filter(OpsEvent.severity == severity)
        if from_ts:
            query = query.filter(OpsEvent.timestamp >= from_ts)
        if to_ts:
            query = query.filter(OpsEvent.timestamp <= to_ts)

        query = query.order_by(OpsEvent.timestamp.desc())

        if zero_results_only:
            events = [
                event
                for event in query.all()
                if event.event_type == "search_result" and int(event.payload.get("result_count") or 0) == 0
            ]
            return events[offset: offset + limit]

        return query.offset(offset).limit(limit).all()

    def list_zero_result_clusters(self, db: Session, limit: int = 20, offset: int = 0) -> List[ZeroResultCluster]:
        return (
            db.query(ZeroResultCluster)
            .order_by(ZeroResultCluster.hit_count.desc(), ZeroResultCluster.last_seen.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def upsert_zero_result_cluster(self, db: Session, query_text: str, timestamp: datetime) -> ZeroResultCluster:
        cluster_intent = normalize_query_intent(query_text)
        cluster = (
            db.query(ZeroResultCluster)
            .filter(ZeroResultCluster.cluster_intent == cluster_intent)
            .one_or_none()
        )

        if cluster:
            examples = list(cluster.query_examples or [])
            if query_text not in examples:
                examples.append(query_text)
            cluster.query_examples = examples
            cluster.hit_count += 1
            cluster.last_seen = timestamp
        else:
            cluster = ZeroResultCluster(
                cluster_intent=cluster_intent,
                query_examples=[query_text],
                hit_count=1,
                first_seen=timestamp,
                last_seen=timestamp,
                status="open",
                recommended_runbook="catalog_qa_agent",
            )
            db.add(cluster)

        db.commit()
        db.refresh(cluster)
        return cluster

    def _search_result_severity(self, provider_result: Dict[str, Any]) -> str:
        error_type = provider_result.get("error_type")
        if error_type in {"timeout", "provider_error"}:
            return "critical"
        if error_type == "client_error":
            return "warning"
        if int(provider_result.get("result_count") or 0) == 0:
            return "warning"
        return "info"

    def _sync_catalog_diff_to_ocs(self, signal: CatalogDiffRequest, product: Optional[Dict[str, Any]]) -> None:
        if self.catalog_client is None:
            return

        operation = signal.operation.upper()
        if operation in {"INSERT", "UPDATE"}:
            if product is None:
                raise CatalogSyncError(f"Cannot sync {operation} for {signal.product_id} without product data")
            if not self.catalog_client.add_product(product):
                raise CatalogSyncError(f"OCS upsert failed for {signal.product_id}")
        elif operation == "DELETE":
            if not self.catalog_client.delete_product(signal.product_id):
                raise CatalogSyncError(f"OCS delete failed for {signal.product_id}")
        else:
            raise CatalogSyncError(f"Unsupported catalog operation {signal.operation}")

        if not self.catalog_client.flush_config():
            raise CatalogSyncError(f"OCS flush_config failed for {signal.product_id}")

    def _search_event_id(self, tenant: str, query_text: str, timestamp: datetime) -> str:
        timestamp_minute = timestamp.replace(second=0, microsecond=0)
        digest = hashlib.sha256(f"{tenant}|{query_text}|{timestamp_minute.isoformat()}".encode("utf-8")).hexdigest()[:16]
        return f"SR-{timestamp:%Y%m%d}-{digest}"

    def _uuid_event_id(self, prefix: str, timestamp: datetime) -> str:
        return f"{prefix}-{timestamp:%Y%m%d}-{uuid.uuid4().hex[:8]}"

    def _insert_event_ignore_duplicate(self, db: Session, event: OpsEvent) -> Tuple[OpsEvent, bool]:
        try:
            db.add(event)
            db.commit()
            db.refresh(event)
            return event, True
        except IntegrityError:
            db.rollback()
            existing = db.query(OpsEvent).filter(OpsEvent.event_id == event.event_id).one()
            return existing, False

    def _load_batch_queries(self, queries_file: str) -> List[Dict[str, Any]]:
        path = Path(queries_file)
        if not path.is_absolute():
            project_root = Path(__file__).resolve().parents[2]
            path = project_root / path
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, dict):
            queries = data.get("queries")
            if not isinstance(queries, list):
                raise ValueError("Batch query file object must contain a queries array")
            normalized_queries = []
            for index, item in enumerate(queries, start=1):
                if isinstance(item, str):
                    normalized_queries.append({"query_id": f"Q{index:03d}", "query_text": item})
                elif isinstance(item, dict):
                    normalized_queries.append(item)
            return normalized_queries
        if not isinstance(data, list):
            raise ValueError("Batch query file must contain a JSON array or an object with a queries array")
        return [item for item in data if isinstance(item, dict)]
