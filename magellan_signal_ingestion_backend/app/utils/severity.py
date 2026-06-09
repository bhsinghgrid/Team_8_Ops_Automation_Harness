from __future__ import annotations

from app.schemas.signal_schema import CatalogDiffRequest, RuleDiffRequest


EMBEDDING_SENSITIVE_FIELDS = {
    "title",
    "description",
    "category",
    "brand",
    "attributes.waterproof",
    "attributes.terrain",
    "attributes.material",
    "attributes.size_range",
    "attributes.capacity_liters",
    "attributes.laptop_size",
    "attributes.temp_rating_c",
}


def determine_catalog_severity(request: CatalogDiffRequest) -> str:
    operation = request.operation.upper()
    if operation == "DELETE":
        return "critical"
    if operation == "INSERT" and request.missing_attributes:
        return "critical"
    if operation == "UPDATE" and any(field in EMBEDDING_SENSITIVE_FIELDS for field in request.changed_fields):
        return "warning"
    return "info"


def determine_rule_severity(request: RuleDiffRequest) -> str:
    operation = request.operation.upper()
    rule_type = request.rule_type
    if request.oos_conflicts:
        return "critical"
    if operation == "DELETE":
        return "warning"
    if operation == "INSERT" and rule_type == "boost":
        return "warning"
    if operation == "UPDATE" and rule_type == "boost":
        return "warning"
    if operation == "INSERT" and rule_type == "suppress":
        return "warning"
    if (
        operation == "UPDATE"
        and "active" in request.changed_fields
        and (request.after_state or {}).get("active") is True
        and rule_type == "boost"
    ):
        return "warning"
    return "info"
