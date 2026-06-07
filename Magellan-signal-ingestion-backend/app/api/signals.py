from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.providers.ocs_catalog import OCSCatalogClient, OCSClientError
from app.providers.product_state_manager import ProductStateError, ProductStateManager
from app.providers.rule_state_manager import RuleStateError, RuleStateManager
from app.schemas.signal_schema import (
    BatchSearchRequest,
    CatalogDiffRequest,
    CatalogDiffResponse,
    OpsEventResponse,
    RuleDiffRequest,
    RuleDiffResponse,
    SearchBatchResponse,
    SearchSignalRequest,
    ZeroResultClusterResponse,
)
from app.services.ingestion_service import CatalogSyncError, IngestionService

router = APIRouter()


def get_rule_state_manager() -> RuleStateManager:
    return RuleStateManager()


def get_product_state_manager() -> ProductStateManager:
    return ProductStateManager()


def get_catalog_client():
    with OCSCatalogClient(
        base_url=settings.OCS_SEARCH_URL,
        tenant=settings.OCS_TENANT,
        timeout=settings.REQUEST_TIMEOUT_SECONDS,
    ) as client:
        yield client


def event_response(event, created: bool = True) -> OpsEventResponse:
    return OpsEventResponse(
        event_id=event.event_id,
        event_type=event.event_type,
        source_capability=event.source_capability,
        severity=event.severity,
        timestamp=event.timestamp,
        provider=event.provider,
        tenant=event.tenant,
        payload=event.payload,
        created=created,
    )


@router.post("/search", response_model=OpsEventResponse)
async def ingest_search_signal(
    payload: SearchSignalRequest,
    db: Session = Depends(get_db),
):
    service = IngestionService()
    event, created = await service.ingest_search(db, payload)
    if event is None:
        raise HTTPException(status_code=502, detail="Malformed OCS response; no event persisted")
    return event_response(event, created)


@router.post("/search/batch", response_model=SearchBatchResponse)
async def ingest_search_batch(
    payload: BatchSearchRequest = BatchSearchRequest(),
    db: Session = Depends(get_db),
):
    service = IngestionService()
    result = await service.ingest_search_batch(db, payload)
    return SearchBatchResponse(**result)


@router.get("/search", response_model=List[OpsEventResponse])
async def list_search_signals(
    event_type: Optional[str] = Query(default=None, pattern="^(search_result|catalog_delta|rule_diff)$"),
    severity: Optional[str] = Query(default=None, pattern="^(critical|warning|info)$"),
    zero_results_only: bool = False,
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    service = IngestionService()
    events = service.list_events(
        db=db,
        event_type=event_type,
        severity=severity,
        zero_results_only=zero_results_only,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
        offset=offset,
    )
    return [event_response(event) for event in events]


@router.get("/zero-results", response_model=List[ZeroResultClusterResponse])
async def list_zero_result_clusters(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    service = IngestionService()
    return service.list_zero_result_clusters(db, limit=limit, offset=offset)


@router.post("/catalog-diff", response_model=CatalogDiffResponse, status_code=status.HTTP_201_CREATED)
async def ingest_catalog_delta(
    payload: CatalogDiffRequest,
    db: Session = Depends(get_db),
    product_state_manager: ProductStateManager = Depends(get_product_state_manager),
    catalog_client: OCSCatalogClient = Depends(get_catalog_client),
):
    service = IngestionService(product_state_manager=product_state_manager, catalog_client=catalog_client)
    try:
        event, _created = service.ingest_catalog_diff(db, payload)
    except ProductStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (CatalogSyncError, OCSClientError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return CatalogDiffResponse(
        event_id=event.event_id,
        severity=event.severity,
        message=f"Catalog delta ingested and applied for {payload.product_id}",
    )


@router.post("/rule-diff", response_model=RuleDiffResponse, status_code=status.HTTP_201_CREATED)
async def ingest_rule_diff(
    payload: RuleDiffRequest,
    db: Session = Depends(get_db),
    rule_state_manager: RuleStateManager = Depends(get_rule_state_manager),
):
    service = IngestionService(rule_state_manager=rule_state_manager)
    try:
        event, _created = service.ingest_rule_diff(db, payload)
    except RuleStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return RuleDiffResponse(
        event_id=event.event_id,
        severity=event.severity,
        message=f"Rule diff ingested and applied for {payload.rule_id}",
    )
