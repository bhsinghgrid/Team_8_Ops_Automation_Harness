"""Pydantic schemas for RCA signal ingestion and LLM output validation."""

from .shared_ingress import IncomingSignal
from .rca_schema import EvidencePackOutput

# Keep a backwards-compatible name `RCAResult` if other modules import it
RCAResult = EvidencePackOutput

__all__ = ["IncomingSignal", "RCAResult", "EvidencePackOutput"]
