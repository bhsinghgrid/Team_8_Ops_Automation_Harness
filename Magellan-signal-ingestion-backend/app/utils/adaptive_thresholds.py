import math
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.observation import TenantMetricBaseline

def evaluate_adaptive_metric(
    db: Session, 
    tenant: str, 
    metric_name: str, 
    current_value: float, 
    alpha: float = 0.2, 
    min_samples: int = 5
) -> tuple[float, float]:
    """
    Updates the Exponentially Weighted Moving Average (EWMA) and Variance for a metric.
    Returns a tuple of (z_score, current_baseline_ewma).
    """
    record = db.query(TenantMetricBaseline).filter_by(tenant=tenant, metric_name=metric_name).first()

    if not record:
        # First time seeing this metric for the tenant, establish the baseline
        record = TenantMetricBaseline(
            tenant=tenant,
            metric_name=metric_name,
            ewma_value=float(current_value),
            ewma_variance=0.0,
            sample_count=1,
            last_updated=datetime.now(timezone.utc)
        )
        db.add(record)
        db.commit()
        return 0.0, float(current_value)

    # Calculate Z-Score against the *previous* baseline
    stddev = math.sqrt(record.ewma_variance)
    z_score = 0.0
    if stddev > 0:
        z_score = (current_value - record.ewma_value) / stddev

    # Update EWMA and Variance for the *next* evaluation
    diff = current_value - record.ewma_value
    new_ewma = record.ewma_value + (alpha * diff)
    new_variance = (1 - alpha) * (record.ewma_variance + (alpha * diff ** 2))

    record.ewma_value = new_ewma
    record.ewma_variance = new_variance
    record.sample_count += 1
    record.last_updated = datetime.now(timezone.utc)
    db.commit()

    # Don't alert if we haven't gathered enough samples to form a stable baseline
    if record.sample_count < min_samples:
        return 0.0, record.ewma_value

    return z_score, record.ewma_value
