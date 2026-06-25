from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.observation import OpsEvent, SearchLog # Ensure SearchLog is here
from app.schemas.detected_signal import DetectedSignal
from app.schemas.search_log_schema import SearchLogBatchRequest, SearchLogEntry
from app.services.detection_engine import DetectionEngine
from app.services.log_parser import parse_log_batch
from app.services.config_service import get_tenant_config

router = APIRouter()


class FileIngestRequest(BaseModel):
    file_path: str


def load_logs_from_db(db: Session, start_time: datetime, end_time: datetime) -> List[SearchLogEntry]:
    db_records = db.query(SearchLog).filter(
        SearchLog.timestamp >= start_time,
        SearchLog.timestamp <= end_time
    ).all()
    
    logs = []
    for record in db_records:
        try:
            logs.append(SearchLogEntry.model_validate(record.payload))
        except Exception:
            continue
    return logs


@router.post("/ingest", response_model=List[DetectedSignal])
def ingest_log_entry(entry: SearchLogEntry, db: Session = Depends(get_db)):
    """
    Ingest a single SearchLogEntry, persist it, execute detection engine on 
    the 5-minute sliding window ending at this entry, and return any detected signals.
    """
    tenant_config = get_tenant_config(db, entry.tenant)
    engine = DetectionEngine(config=tenant_config)
    # 1. Persist raw log
    engine.persist_raw_logs(db, [entry])

    # 2. Query all logs in the 5-minute window leading up to this log
    window_end = entry.timestamp
    window_start = window_end - timedelta(minutes=5)
    window_logs = load_logs_from_db(db, window_start, window_end)

    # 3. Run detection
    signals = engine.run(window_logs, db=db)

    # 4. Persist detected signals
    engine.persist_signals(db, signals)

    return signals


@router.post("/ingest/batch")
def ingest_log_batch(request: SearchLogBatchRequest, db: Session = Depends(get_db)):
    """
    Ingest a batch of SearchLogEntry objects, run detection across the batch,
    and persist results.
    """
    base_engine = DetectionEngine()
    inserted = base_engine.persist_raw_logs(db, request.logs)
    
    # Group logs by tenant to apply specific configs
    tenant_logs = {}
    for log in request.logs:
        tenant_logs.setdefault(log.tenant, []).append(log)
        
    all_signals = []
    for tenant, logs in tenant_logs.items():
        tenant_config = get_tenant_config(db, tenant)
        engine = DetectionEngine(config=tenant_config)
        signals = engine.run(logs, db=db)
        all_signals.extend(signals)
        
    base_engine.persist_signals(db, all_signals)

    return {
        "status": "success",
        "ingested_logs": inserted,
        "total_logs": len(request.logs),
        "detected_signals_count": len(all_signals),
        "signals": all_signals
    }


@router.post("/ingest/file")
def ingest_log_file(request: FileIngestRequest, db: Session = Depends(get_db)):
    """
    Accepts a filepath to a JSONL log file, parses all log lines, sniffs formats,
    runs detection engine on the parsed batch, and persists all logs and signals.
    """
    path = Path(request.file_path)
    if not path.is_absolute():
        project_root = Path(__file__).resolve().parents[2]
        path = project_root / path

    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found at path: {path}")

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    successes, errors = parse_log_batch(lines)

    base_engine = DetectionEngine()
    inserted = base_engine.persist_raw_logs(db, successes)
    
    tenant_logs = {}
    for log in successes:
        tenant_logs.setdefault(log.tenant, []).append(log)

    all_signals = []
    for tenant, logs in tenant_logs.items():
        tenant_config = get_tenant_config(db, tenant)
        engine = DetectionEngine(config=tenant_config)
        signals = engine.run(logs, db=db)
        all_signals.extend(signals)

    base_engine.persist_signals(db, all_signals)

    return {
        "status": "success",
        "parsed_successfully": len(successes),
        "failed_parsing": len(errors),
        "ingested_logs": inserted,
        "detected_signals_count": len(all_signals),
        "errors": errors[:50]
    }


@router.get("/signals")
def list_detected_signals(
    signal_type: Optional[str] = None,
    severity: Optional[str] = None,
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List detected passive signals (OpsEvents) with optional filtering.
    """
    query = db.query(OpsEvent).filter(OpsEvent.event_type == "passive_signal")
    if severity:
        query = query.filter(OpsEvent.severity == severity)
    if from_ts:
        query = query.filter(OpsEvent.timestamp >= from_ts)
    if to_ts:
        query = query.filter(OpsEvent.timestamp <= to_ts)

    query = query.order_by(OpsEvent.timestamp.desc())
    events = query.offset(offset).limit(limit).all()

    signals = []
    for event in events:
        payload = event.payload
        if signal_type and payload.get("signal_type") != signal_type:
            continue
        # Inject event_id into payload for client convenience
        payload["event_id"] = event.event_id
        signals.append(payload)

    return signals


@router.get("/stats")
def get_stats(
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Aggregate statistics for a time window based on raw search logs.
    """
    query = db.query(SearchLog)
    if from_ts:
        query = query.filter(SearchLog.timestamp >= from_ts)
    if to_ts:
        query = query.filter(SearchLog.timestamp <= to_ts)

    logs = query.all()
    if not logs:
        return {
            "total_logs": 0,
            "error_rate": 0.0,
            "avg_latency_ms": 0.0,
            "ctr": 0.0
        }

    total_logs = len(logs)
    error_count = sum(1 for log in logs if log.has_error)
    avg_latency = sum(log.latency_ms for log in logs) / total_logs

    ctr_eligible = [log for log in logs if log.status_code == 200 and log.result_count > 0]
    if ctr_eligible:
        ctr_clicked = sum(1 for log in ctr_eligible if log.click_count > 0)
        ctr = ctr_clicked / len(ctr_eligible)
    else:
        ctr = 0.0

    return {
        "total_logs": total_logs,
        "error_rate": error_count / total_logs,
        "avg_latency_ms": avg_latency,
        "ctr": ctr
    }

@router.get("/raw", response_model=List[Dict[str, Any]])
def list_raw_logs(
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Lists raw search logs from the database with optional time filtering.
    Returns the full payload of each log.
    """
    query = db.query(SearchLog)

    if from_ts:
        query = query.filter(SearchLog.timestamp >= from_ts)
    if to_ts:
        query = query.filter(SearchLog.timestamp <= to_ts)

    query = query.order_by(SearchLog.timestamp.desc())
    
    raw_logs = query.offset(offset).limit(limit).all()

    return [log.payload for log in raw_logs]
