from datetime import datetime
from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field

Severity = Literal["critical", "warning", "info"]


class DetectedSignal(BaseModel):
    signal_type: str = Field(..., description="The type of detected signal, e.g. latency_spike, zero_results, low_ctr, etc.")
    tenant: str = Field(..., description="The tenant associated with the signal.")
    severity: Severity = Field(..., description="The severity level of the alert.")
    summary: str = Field(..., description="Human-readable description of the detected signal.")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting metrics or data for the signal.")
    affected_queries: List[str] = Field(default_factory=list, description="List of search query strings related to this signal.")
    window_start: datetime = Field(..., description="The start of the aggregation time window.")
    window_end: datetime = Field(..., description="The end of the aggregation time window.")
