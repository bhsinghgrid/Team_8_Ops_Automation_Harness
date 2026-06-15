import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Tuple

from pydantic import ValidationError
from app.schemas.search_log_schema import SearchLogEntry

logger = logging.getLogger(__name__)


class LogParseError(ValueError):
    pass


def parse_log_line(raw: str) -> SearchLogEntry:
    """
    Parse a single raw JSON log line, validation against SearchLogEntry schema.
    Sniffs between the new nested format and the legacy flat format.
    """
    raw_str = raw.strip()
    if not raw_str:
        raise LogParseError("Empty log line")

    try:
        data = json.loads(raw_str)
    except json.JSONDecodeError as e:
        raise LogParseError(f"Invalid JSON: {str(e)}") from e

    if not isinstance(data, dict):
        raise LogParseError("Log entry must be a JSON object")

    # Sniff format
    if "query" in data and isinstance(data["query"], dict):
        # Nested format
        try:
            return SearchLogEntry.model_validate(data)
        except ValidationError as e:
            raise LogParseError(f"Validation error: {str(e)}") from e
    elif "query_text" in data:
        # Legacy flat format mapping
        try:
            timestamp = data.get("timestamp")
            source = data.get("source", "legacy_search")
            tenant = data.get("tenant", "default")
            request_id = data.get("request_id", "")
            session_id = data.get("session_id", "")
            user_id_hash = data.get("user_id_hash", "")
            error = data.get("error_type") or data.get("error")

            # Query Block
            query_text = data.get("query_text", "")
            normalized_text = data.get("normalized_text")
            if not normalized_text and query_text:
                words = [w for w in re.findall(r"[a-z0-9]+", query_text.lower()) if w not in {"a", "the", "for", "with"}]
                normalized_text = " ".join(words) if words else None

            query_block = {
                "text": query_text,
                "normalized_text": normalized_text,
                "filters": data.get("filters") or {},
                "sort": data.get("sort"),
            }

            # Response Block
            top_product_ids = data.get("top_product_ids") or []
            results = [
                {
                    "product_id": pid,
                    "rank": i + 1,
                    "score": 0.0,
                }
                for i, pid in enumerate(top_product_ids)
            ]
            response_block = {
                "status_code": data.get("status_code", 200),
                "latency_ms": data.get("latency_ms", 0),
                "result_count": data.get("result_count", len(top_product_ids)),
                "results": results,
            }

            # Interaction Block
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                else:
                    dt = datetime.now(timezone.utc)
            except Exception:
                dt = datetime.now(timezone.utc)

            click_dt = (dt + timedelta(seconds=15)).isoformat().replace("+00:00", "Z")
            cart_dt = (dt + timedelta(seconds=45)).isoformat().replace("+00:00", "Z")

            clicked_product_ids = data.get("clicked_product_ids") or []
            clicks = [
                {
                    "product_id": pid,
                    "rank": top_product_ids.index(pid) + 1 if pid in top_product_ids else 1,
                    "timestamp": click_dt,
                }
                for pid in clicked_product_ids
            ]

            cart_add_product_ids = data.get("cart_add_product_ids") or []
            cart_adds = [
                {
                    "product_id": pid,
                    "rank": top_product_ids.index(pid) + 1 if pid in top_product_ids else 1,
                    "timestamp": cart_dt,
                }
                for pid in cart_add_product_ids
            ]

            interaction_block = {
                "clicks": clicks,
                "cart_adds": cart_adds,
            }

            # Context Block
            context_block = {
                "device_type": data.get("device_type", "unknown"),
                "channel": data.get("channel", "unknown"),
                "locale": data.get("locale", "unknown"),
            }

            nested_data = {
                "timestamp": timestamp,
                "source": source,
                "tenant": tenant,
                "request_id": request_id,
                "session_id": session_id,
                "user_id_hash": user_id_hash,
                "query": query_block,
                "response": response_block,
                "interaction": interaction_block,
                "context": context_block,
                "error": error,
            }

            return SearchLogEntry.model_validate(nested_data)
        except ValidationError as e:
            raise LogParseError(f"Validation error mapping legacy log: {str(e)}") from e
        except Exception as e:
            raise LogParseError(f"Error mapping legacy log: {str(e)}") from e
    else:
        raise LogParseError("Unknown log format: missing both 'query' and 'query_text'")


def parse_log_batch(lines: Iterable[str]) -> Tuple[List[SearchLogEntry], List[dict]]:
    """
    Parses a batch of log lines.
    Returns:
        Tuple[List[SearchLogEntry], List[dict]]: list of parsed entries, list of error dicts
    """
    successes = []
    errors = []
    for i, line in enumerate(lines):
        line_str = line.strip()
        if not line_str:
            continue
        try:
            entry = parse_log_line(line_str)
            successes.append(entry)
        except LogParseError as e:
            errors.append({"line_number": i + 1, "error": str(e), "raw": line_str})
    return successes, errors
