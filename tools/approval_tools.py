"""Approval and governance gating tools."""

from __future__ import annotations

def requires_human_approval(capability: str, gap_type: str = "") -> bool:
    """
    Implements the g(a,E,Pi) safety gating equation based on risk thresholds.
    Returns True if human approval is required, False if the agent can auto-execute.
    """
    capability_lower = capability.lower()
    gap_type_lower = gap_type.lower()
    
    # Tier 1: Low-Risk / Auto-Close -> No human needed
    # e.g., "Catalog Completeness Gaps", "Stale Embeddings"
    if "catalog" in capability_lower or "stale embeddings" in capability_lower or "stale" in gap_type_lower:
        return False
        
    # Tier 2 & 3: High-Risk (MXP/Merchandising, Autocomplete drift, Multimodal) 
    # or Infrastructure (Vector mismatch) -> Human gate required
    # Any other undefined/unknown defaults to True for safety.
    return True

def determine_approval_gate(capability: str, gap_type: str = "") -> str:
    """Returns a description of the approval gate."""
    if requires_human_approval(capability, gap_type):
        if "mxp" in capability.lower() or "merchandising" in capability.lower():
            return "Requires Merchandising Owner sign-off before deployment."
        elif "infrastructure" in capability.lower() or "vector" in capability.lower():
            return "Blocked: Infrastructure Invariant Breach. Requires Platform Engineering."
        elif "autocomplete" in capability.lower() or "multimodal" in capability.lower():
            return "Shadow Replay only. Requires Human Search Lead to review brand impact."
        return "Requires human sign-off for safety."
    return "Auto-Close Allowed: Low-risk envelope."
