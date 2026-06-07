"""Recursive diff helpers for shadow-testing comparisons."""

from __future__ import annotations

from collections import Counter
from typing import Any

from tools.index_analysis_tools import compact_value


def _normalize_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return list(value)
    return value


def _join_path(base: str, segment: str) -> str:
    if not base or base == "$":
        return segment
    if segment.startswith("["):
        return f"{base}{segment}"
    return f"{base}.{segment}"


def _append_diff(
    diffs: list[dict[str, Any]],
    *,
    path: str,
    change_type: str,
    baseline: Any,
    candidate: Any,
) -> None:
    diffs.append(
        {
            "path": path or "$",
            "changeType": change_type,
            "baseline": compact_value(baseline),
            "candidate": compact_value(candidate),
        }
    )


def _diff_values(
    baseline: Any,
    candidate: Any,
    *,
    path: str,
    diffs: list[dict[str, Any]],
    max_diffs: int,
) -> None:
    if len(diffs) >= max_diffs:
        return

    baseline = _normalize_value(baseline)
    candidate = _normalize_value(candidate)

    if type(baseline) is not type(candidate):
        _append_diff(
            diffs,
            path=path,
            change_type="type_changed",
            baseline=baseline,
            candidate=candidate,
        )
        return

    if isinstance(baseline, dict):
        keys = sorted(set(baseline) | set(candidate))
        for key in keys:
            if len(diffs) >= max_diffs:
                return
            next_path = _join_path(path, str(key))
            if key not in baseline:
                _append_diff(
                    diffs,
                    path=next_path,
                    change_type="added",
                    baseline=None,
                    candidate=candidate[key],
                )
                continue
            if key not in candidate:
                _append_diff(
                    diffs,
                    path=next_path,
                    change_type="removed",
                    baseline=baseline[key],
                    candidate=None,
                )
                continue
            _diff_values(
                baseline[key],
                candidate[key],
                path=next_path,
                diffs=diffs,
                max_diffs=max_diffs,
            )
        return

    if isinstance(baseline, list):
        max_len = max(len(baseline), len(candidate))
        for index in range(max_len):
            if len(diffs) >= max_diffs:
                return
            next_path = _join_path(path, f"[{index}]")
            if index >= len(baseline):
                _append_diff(
                    diffs,
                    path=next_path,
                    change_type="added",
                    baseline=None,
                    candidate=candidate[index],
                )
                continue
            if index >= len(candidate):
                _append_diff(
                    diffs,
                    path=next_path,
                    change_type="removed",
                    baseline=baseline[index],
                    candidate=None,
                )
                continue
            _diff_values(
                baseline[index],
                candidate[index],
                path=next_path,
                diffs=diffs,
                max_diffs=max_diffs,
            )
        return

    if baseline != candidate:
        _append_diff(
            diffs,
            path=path,
            change_type="changed",
            baseline=baseline,
            candidate=candidate,
        )


def diff_shadow_responses(
    baseline: Any,
    candidate: Any,
    *,
    max_diffs: int = 200,
) -> list[dict[str, Any]]:
    """Return a recursive, field-level diff between two JSON-like payloads."""

    diffs: list[dict[str, Any]] = []
    _diff_values(baseline, candidate, path="$", diffs=diffs, max_diffs=max_diffs)
    return diffs


def summarize_shadow_diffs(diffs: list[dict[str, Any]], *, max_paths: int = 12) -> dict[str, Any]:
    """Summarize the response diff output for reports and agent handoffs."""

    counts = Counter(str(diff.get("changeType", "unknown")) for diff in diffs)
    paths = [str(diff.get("path", "$")) for diff in diffs]
    return {
        "diffCount": len(diffs),
        "addedCount": counts.get("added", 0),
        "removedCount": counts.get("removed", 0),
        "changedCount": counts.get("changed", 0),
        "typeChangedCount": counts.get("type_changed", 0),
        "responseEquivalent": len(diffs) == 0,
        "truncated": len(diffs) >= max_paths and len(paths) > max_paths,
        "topPaths": paths[:max_paths],
    }
