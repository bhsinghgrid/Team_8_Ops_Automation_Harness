"""Owner and escalation path tools."""

from __future__ import annotations

from typing import Any, Mapping


CAPABILITY_OWNERS = {
    "catalog_completeness": {
        "primary_owner": "Catalog data owner",
        "secondary_owner": "Indexing platform owner",
        "approver": "Commerce data lead",
    },
    "search_relevance": {
        "primary_owner": "Search relevance owner",
        "secondary_owner": "Search platform owner",
        "approver": "Search engineering lead",
    },
    "search_performance": {
        "primary_owner": "Search performance owner",
        "secondary_owner": "Search platform owner",
        "approver": "Search engineering lead",
    },
    "semantic_search": {
        "primary_owner": "Search relevance owner",
        "secondary_owner": "Search platform owner",
        "approver": "Search engineering lead",
    },
    "semantic_retrieval": {
        "primary_owner": "Search relevance owner",
        "secondary_owner": "Vector platform owner",
        "approver": "Search engineering lead",
    },
    "catalog": {
        "primary_owner": "Catalog data owner",
        "secondary_owner": "Indexing platform owner",
        "approver": "Commerce data lead",
    },
    "autocomplete": {
        "primary_owner": "Autocomplete owner",
        "secondary_owner": "Search platform owner",
        "approver": "Search engineering lead",
    },
    "autocomplete_coverage": {
        "primary_owner": "Autocomplete owner",
        "secondary_owner": "Search platform owner",
        "approver": "Search engineering lead",
    },
    "autocomplete_freshness": {
        "primary_owner": "Autocomplete owner",
        "secondary_owner": "Search platform owner",
        "approver": "Search engineering lead",
    },
    "semantic_index": {
        "primary_owner": "Vector index owner",
        "secondary_owner": "Search platform owner",
        "approver": "Search engineering lead",
    },
    "personalization": {
        "primary_owner": "Personalization owner",
        "secondary_owner": "Feature platform owner",
        "approver": "ML engineering lead",
    },
    "merchandising_controls": {
        "primary_owner": "Merchandising operations owner",
        "secondary_owner": "Rule platform owner",
        "approver": "Commerce product lead",
    },
    "merchandising_governance": {
        "primary_owner": "Merchandising operations owner",
        "secondary_owner": "Rule platform owner",
        "approver": "Commerce product lead",
    },
    "search_api": {
        "primary_owner": "Search API owner",
        "secondary_owner": "Platform owner",
        "approver": "Engineering lead",
    },
    "browse_intent": {
        "primary_owner": "Search experience owner",
        "secondary_owner": "Search platform owner",
        "approver": "Search product lead",
    },
}


def resolve_owner_chain(capability: str, runbook_owner: Mapping[str, Any] | None = None) -> dict[str, str]:
    runbook_owner = dict(runbook_owner or {})
    owner_defaults = CAPABILITY_OWNERS.get(
        capability,
        {
            "primary_owner": runbook_owner.get("primary_owner", "Application owner"),
            "secondary_owner": runbook_owner.get("secondary_owner", "Platform owner"),
            "approver": runbook_owner.get("approver", "Engineering lead"),
        },
    )
    return {
        "primary_owner": str(runbook_owner.get("primary_owner") or owner_defaults["primary_owner"]),
        "secondary_owner": str(runbook_owner.get("secondary_owner") or owner_defaults["secondary_owner"]),
        "approver": str(runbook_owner.get("approver") or owner_defaults["approver"]),
    }


def build_escalation_path(
    primary_owner: str,
    secondary_owner: str,
    approver: str,
    blocked_reason: str | None = None,
) -> list[str]:
    path = [primary_owner, secondary_owner, approver]
    if blocked_reason:
        path.append("Release operator")
    return path
