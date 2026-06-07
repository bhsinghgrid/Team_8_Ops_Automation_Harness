"""Capability grouping tools."""

from .capability_mapping_tools import infer_capability_from_signal
from .impact_tools import higher_severity, score_signal, signal_to_capability


def group_by_capability(signals):
    grouped = {}

    for signal in signals:
        capability = signal_to_capability(signal)
        if capability == "unknown":
            capability = infer_capability_from_signal(signal)
        item = grouped.setdefault(
            capability,
            {
                "capability": capability,
                "impactScore": 0,
                "maxSeverity": "low",
                "signals": [],
                "reasons": [],
            },
        )

        item["impactScore"] += score_signal(signal)
        item["maxSeverity"] = higher_severity(item["maxSeverity"], signal.get("severity", "medium"))
        item["signals"].append(signal.get("id"))
        item["reasons"].append(signal.get("summary", signal.get("type")))

    return grouped


def rank_capabilities(grouped):
    return sorted(grouped.values(), key=lambda item: item["impactScore"], reverse=True)
