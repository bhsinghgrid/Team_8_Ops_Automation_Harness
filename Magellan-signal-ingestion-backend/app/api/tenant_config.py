from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.observation import TenantConfig
from app.services.config_service import get_tenant_config

router = APIRouter()

@router.get("/{tenant}")
def get_config(tenant: str, db: Session = Depends(get_db)):
    """Retrieve the dynamic detection configuration for a specific tenant."""
    return get_tenant_config(db, tenant)

@router.put("/{tenant}")
def update_config(tenant: str, payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Update or create the detection configuration overrides for a specific tenant."""
    record = db.query(TenantConfig).filter(TenantConfig.tenant == tenant).first()
    if record:
        record.config_payload = payload
        record.updated_at = datetime.now(timezone.utc)
    else:
        record = TenantConfig(
            tenant=tenant,
            config_payload=payload,
            updated_at=datetime.now(timezone.utc)
        )
        db.add(record)
    
    db.commit()
    return {"status": "success", "tenant": tenant, "config": get_tenant_config(db, tenant)}
