from __future__ import annotations

import re
from typing import Any, Dict, List

from deepdiff import DeepDiff


REQUIRED_ATTRIBUTES = {
    "footwear": ["waterproof", "terrain", "material", "size_range"],
    "bags": ["capacity_liters", "laptop_size", "material", "waterproof"],
    "outerwear": ["waterproof", "material", "size_range", "weight_grams"],
    "electronics": ["battery_hours", "waterproof", "display"],
    "camping": ["temp_rating_c", "material", "waterproof"],
}

PATH_TOKEN_PATTERN = re.compile(r"\['([^']+)'\]|\[(\d+)\]")


def compute_diff(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    diff = DeepDiff(before, after, ignore_order=False)
    before_values: Dict[str, Any] = {}
    after_values: Dict[str, Any] = {}

    for path, change in diff.get("values_changed", {}).items():
        field = deepdiff_path_to_dot(path)
        before_values[field] = change.get("old_value")
        after_values[field] = change.get("new_value")

    for path, change in diff.get("type_changes", {}).items():
        field = deepdiff_path_to_dot(path)
        before_values[field] = change.get("old_value")
        after_values[field] = change.get("new_value")

    for path in diff.get("dictionary_item_added", []):
        field = deepdiff_path_to_dot(path)
        before_values[field] = None
        after_values[field] = get_by_dot_path(after, field)

    for path in diff.get("dictionary_item_removed", []):
        field = deepdiff_path_to_dot(path)
        before_values[field] = get_by_dot_path(before, field)
        after_values[field] = None

    for path, value in diff.get("iterable_item_added", {}).items():
        field = deepdiff_path_to_dot(path)
        before_values[field] = None
        after_values[field] = value

    for path, value in diff.get("iterable_item_removed", {}).items():
        field = deepdiff_path_to_dot(path)
        before_values[field] = value
        after_values[field] = None

    changed_fields = sorted(before_values)
    return {
        "changed_fields": changed_fields,
        "before": {field: before_values[field] for field in changed_fields},
        "after": {field: after_values[field] for field in changed_fields},
    }


def deepdiff_path_to_dot(path: str) -> str:
    parts: List[str] = []
    for key, index in PATH_TOKEN_PATTERN.findall(path):
        parts.append(key or index)
    return ".".join(parts)


def get_by_dot_path(value: Dict[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            current = current[int(part)]
        else:
            return None
    return current


def detect_missing_attributes(product: Dict[str, Any]) -> List[str]:
    data = product.get("data") if isinstance(product.get("data"), dict) else {}
    category = str(product.get("category") or data.get("category") or "").lower()
    required = REQUIRED_ATTRIBUTES.get(category, [])
    attributes = product.get("attributes") or {attribute: data.get(attribute) for attribute in required}
    return [
        attribute
        for attribute in required
        if attribute not in attributes or attributes.get(attribute) is None
    ]
