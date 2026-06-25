import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException

from .config import (
    BACKEND_REQUEST_TIMEOUT_SECONDS,
    DATA_API_BEARER_TOKEN,
    DATA_SOURCE_URLS,
)


def request_headers(content_type: str | None = None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if content_type:
        headers["Content-Type"] = content_type
    if DATA_API_BEARER_TOKEN:
        headers["Authorization"] = f"Bearer {DATA_API_BEARER_TOKEN}"
    return headers


def extract_list_payload(payload: Any, keys: list[str]) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    return []


def fetch_remote_list(source_name: str, keys: list[str]) -> list[dict]:
    url = DATA_SOURCE_URLS.get(source_name, "")
    if not url:
        return []

    try:
        request = Request(url, headers=request_headers())
        with urlopen(request, timeout=BACKEND_REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{source_name} source returned HTTP {exc.code}: {url}",
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{source_name} source is not reachable or returned invalid JSON: {url}",
        ) from exc

    return extract_list_payload(payload, keys)


def data_source_status() -> dict[str, dict[str, str | bool]]:
    return {
        name: {
            "configured": bool(url),
            "url": url if url else "not configured",
        }
        for name, url in DATA_SOURCE_URLS.items()
    }
