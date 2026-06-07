"""Signal extraction tools."""


def collect_signals(payload):
    if isinstance(payload.get("signals"), list):
        return payload["signals"]

    signals_by_type = payload.get("signalsByType")
    if isinstance(signals_by_type, dict):
        signals = []
        for items in signals_by_type.values():
            if isinstance(items, list):
                signals.extend(items)
        return signals

    return []


def get_query(payload):
    return payload.get("query")

