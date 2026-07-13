from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

class IncomingSignal(BaseModel):
    """
    The strict payload contract expected from the Phase 1 Signal Ingestion service.
    Acts as the trigger for the RCA routing and context gathering phases.
    """
    signal_id: str = Field(
        ..., 
        description="Unique identifier for the detected anomaly (e.g., 'sig_001')."
    )
    anomaly_type: str = Field(
        ..., 
        description="The categorization of the failure (e.g., 'LOW_CTR', 'ZERO_RESULTS')."
    )
    query_text: str = Field(
        ..., 
        description="The exact normalized search query string that failed."
    )
    impacted_product_id: Optional[str] = Field(
        None, 
        description="The specific product ID failing the metric threshold, if applicable."
    )
    current_metric_value: Optional[float] = Field(
        None, 
        description="The failing metric measurement (e.g., 0.0 for a 0% CTR)."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata related to the anomaly."
    )