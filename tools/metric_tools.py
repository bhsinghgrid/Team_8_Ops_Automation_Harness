"""Shared metric helpers."""

from __future__ import annotations

from typing import Any, Dict


def metric_value(metric_map: Dict[str, Dict[str, Any]], key: str) -> float | None:
    value = metric_map.get(key, {}).get("value")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

