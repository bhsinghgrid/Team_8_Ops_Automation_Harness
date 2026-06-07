from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.signals import event_response
from app.db.database import get_db
from app.schemas.signal_schema import OpsEventResponse, SearchSignalRequest
from app.services.ingestion_service import IngestionService

router = APIRouter()


@router.post("/ingest", response_model=OpsEventResponse)
async def ingest_observation(
    payload: SearchSignalRequest,
    db: Session = Depends(get_db),
):
    service = IngestionService()
    event, created = await service.ingest_search(db, payload)
    if event is None:
        raise HTTPException(status_code=502, detail="Malformed provider response; no observation persisted")
    return event_response(event, created)
