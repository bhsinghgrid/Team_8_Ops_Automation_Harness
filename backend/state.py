from typing import Any


APPROVAL_RECORDS: dict[str, dict[str, Any]] = {}

# Stores activity-level results keyed by workflow_id -> list of activity records
ACTIVITY_RESULTS: dict[str, list[dict[str, Any]]] = {}

