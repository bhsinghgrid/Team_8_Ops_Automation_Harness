import hashlib
import json
from datetime import datetime
from typing import Any, List
from deepdiff import DeepDiff

from app.schemas.detected_signal import DetectedSignal


def has_changed(previous_snapshot: Any, current_snapshot: Any) -> bool:
    """
    Determines if two snapshots differ by comparing their hashes.
    """
    def get_hash(obj: Any) -> str:
        if obj is None:
            return ""
        # Serialize the object to a consistent JSON string
        serialized = json.dumps(obj, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    return get_hash(previous_snapshot) != get_hash(current_snapshot)


def compute_diff_summary(previous_snapshot: Any, current_snapshot: Any) -> dict:
    """
    Computes a granular deep diff between two snapshots and returns a JSON-serializable dictionary.
    """
    if previous_snapshot is None:
        return {"status": "initial_snapshot", "details": "No previous snapshot to compare against. This is the baseline."}
    
    # ignore_order=True helps when list orders change but content remains the same (e.g., product lists)
    diff = DeepDiff(previous_snapshot, current_snapshot, ignore_order=True)
    # DeepDiff provides a convenient .to_json() to ensure complex diff outputs are serializable
    return json.loads(diff.to_json())


class ChangeDetectionAgent:
    """
    A generic agent to detect high-level changes in database states, 
    such as catalog data and MXP rules, without diagnosing the root cause.
    """

    def detect_catalog_delta(
        self,
        tenant: str,
        previous_catalog_snapshot: Any,
        current_catalog_snapshot: Any,
        window_start: datetime,
        window_end: datetime,
    ) -> List[DetectedSignal]:
        """
        Detects if there is a change between catalog snapshots and emits a CATALOG_DELTA signal.
        """
        if has_changed(previous_catalog_snapshot, current_catalog_snapshot):
            diff_summary = compute_diff_summary(previous_catalog_snapshot, current_catalog_snapshot)
            return [
                DetectedSignal(
                    signal_type="CATALOG_DELTA",
                    tenant=tenant,
                    severity="info",
                    summary="A change in the catalog data was detected.",
                    evidence={"changed": True, "diff": diff_summary},
                    affected_queries=[],
                    window_start=window_start,
                    window_end=window_end,
                )
            ]
        return []

    def detect_mxp_rule_diff(
        self,
        tenant: str,
        previous_mxp_snapshot: Any,
        current_mxp_snapshot: Any,
        window_start: datetime,
        window_end: datetime,
    ) -> List[DetectedSignal]:
        """
        Detects if there is a change between MXP rule snapshots and emits an MXP_RULE_DIFF signal.
        """
        if has_changed(previous_mxp_snapshot, current_mxp_snapshot):
            diff_summary = compute_diff_summary(previous_mxp_snapshot, current_mxp_snapshot)
            return [
                DetectedSignal(
                    signal_type="MXP_RULE_DIFF",
                    tenant=tenant,
                    severity="info",
                    summary="A change in the MXP rules was detected.",
                    evidence={"changed": True, "diff": diff_summary},
                    affected_queries=[],
                    window_start=window_start,
                    window_end=window_end,
                )
            ]
        return []
