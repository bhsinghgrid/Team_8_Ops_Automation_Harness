import copy
from sqlalchemy.orm import Session
from app.models.observation import TenantConfig
from app.core.detection_config import DETECTION_DEFAULTS

def get_tenant_config(db: Session, tenant: str) -> dict:
    """
    Retrieves the detection config for a tenant from the database.
    Falls back to DETECTION_DEFAULTS for any missing keys.
    """
    record = db.query(TenantConfig).filter(TenantConfig.tenant == tenant).first()
    config = copy.deepcopy(DETECTION_DEFAULTS)
    
    if record and record.config_payload:
        # Deep merge the tenant specific config overrides
        for key, value in record.config_payload.items():
            if isinstance(value, dict) and key in config:
                config[key].update(value)
            else:
                config[key] = value
                
    return config
