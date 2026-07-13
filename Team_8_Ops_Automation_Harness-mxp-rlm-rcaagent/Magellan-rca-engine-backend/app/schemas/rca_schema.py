from pydantic import BaseModel, Field
from typing import Dict, Any

class RootCauseDetails(BaseModel):
    """A Pydantic model for the root cause details."""
    primary_cause: str = Field(..., description="The primary cause of the issue.")
    confidence_score: float = Field(..., description="The confidence score of the root cause.")
    supporting_evidence: Dict[str, Any] = Field(..., description="The supporting evidence for the root cause.")

class EvidencePackOutput(BaseModel):
    """A Pydantic model for the evidence pack output."""
    signal_id: str = Field(default="placeholder_id", description="The ID of the signal.")
    capability: str = Field(..., description="The capability that was triggered.")
    symptom: str = Field(..., description="The symptom that was observed.")
    root_cause: RootCauseDetails = Field(..., description="The root cause of the issue.")