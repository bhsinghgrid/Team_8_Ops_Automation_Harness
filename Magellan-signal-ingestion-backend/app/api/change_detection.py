from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.change_detection_agent import ChangeDetectionAgent
from app.db.database import get_db
from app.models.observation import SnapshotState
from app.services.detection_engine import DetectionEngine
from app.services.config_service import get_tenant_config

router = APIRouter()

@router.post("/catalog")
async def receive_catalog_snapshot(
    payload: Dict[str, Any],
    tenant: str = "retail_tenant_001",
    db: Session = Depends(get_db)
):
    """
    Receives a snapshot of the catalog. Compares it with the previous snapshot.
    If changed, emits a CATALOG_DELTA signal.
    """
    record = db.query(SnapshotState).filter_by(tenant=tenant, snapshot_type="catalog").first()
    previous_snapshot = record.payload if record else None
    
    agent = ChangeDetectionAgent()
    now = datetime.now(timezone.utc)
    
    signals = agent.detect_catalog_delta(
        tenant=tenant,
        previous_catalog_snapshot=previous_snapshot,
        current_catalog_snapshot=payload,
        window_start=now,
        window_end=now
    )
    
    # Update the stored snapshot
    if record:
        record.payload = payload
        record.last_updated = now
    else:
        new_record = SnapshotState(tenant=tenant, snapshot_type="catalog", payload=payload, last_updated=now)
        db.add(new_record)
    db.commit()
    
    # Persist the signal if one was generated
    if signals:
        tenant_config = get_tenant_config(db, tenant)
        engine = DetectionEngine(config=tenant_config)
        engine.persist_signals(db, signals)
        
    return {
        "status": "success",
        "changed": len(signals) > 0,
        "signals_emitted": len(signals)
    }


@router.post("/rules")
async def receive_mxp_rule_snapshot(
    payload: Dict[str, Any],
    tenant: str = "retail_tenant_001",
    db: Session = Depends(get_db)
):
    """
    Receives a snapshot of the MXP rules. Compares it with the previous snapshot.
    If changed, emits an MXP_RULE_DIFF signal.
    """
    record = db.query(SnapshotState).filter_by(tenant=tenant, snapshot_type="mxp_rules").first()
    previous_snapshot = record.payload if record else None
    
    agent = ChangeDetectionAgent()
    now = datetime.now(timezone.utc)
    
    signals = agent.detect_mxp_rule_diff(
        tenant=tenant,
        previous_mxp_snapshot=previous_snapshot,
        current_mxp_snapshot=payload,
        window_start=now,
        window_end=now
    )
    
    # Update the stored snapshot
    if record:
        record.payload = payload
        record.last_updated = now
    else:
        new_record = SnapshotState(tenant=tenant, snapshot_type="mxp_rules", payload=payload, last_updated=now)
        db.add(new_record)
    db.commit()
    
    # Persist the signal if one was generated
    if signals:
        tenant_config = get_tenant_config(db, tenant)
        engine = DetectionEngine(config=tenant_config)
        engine.persist_signals(db, signals)
        
    return {
        "status": "success",
        "changed": len(signals) > 0,
        "signals_emitted": len(signals)
    }
