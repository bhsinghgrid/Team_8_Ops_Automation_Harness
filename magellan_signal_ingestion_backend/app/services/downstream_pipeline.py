import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.models.observation import OpsEvent

logger = logging.getLogger(__name__)


def downstream_pipeline_enabled() -> bool:
    return settings.DOWNSTREAM_PIPELINE_ENABLED and bool(settings.DOWNSTREAM_PIPELINE_URL.strip())


def build_downstream_event_payload(event: OpsEvent) -> Dict[str, Any]:
    return {
        "source": settings.DOWNSTREAM_PIPELINE_SOURCE,
        "idempotency_key": event.event_id,
        "event_id": event.event_id,
        "event_type": event.event_type,
        "source_capability": event.source_capability,
        "severity": event.severity,
        "timestamp": _isoformat(event.timestamp),
        "ingested_at": _isoformat(event.ingested_at),
        "provider": event.provider,
        "tenant": event.tenant,
        "payload": event.payload,
    }


def dispatch_event_payload(payload: Dict[str, Any]) -> bool:
    client = DownstreamPipelineClient()
    return client.dispatch_event_payload(payload)


class DownstreamPipelineClient:

    def __init__(
        self,
        base_url: Optional[str] = None,
        events_path: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: Optional[float] = None,
        enabled: Optional[bool] = None,
    ):
        self.enabled = settings.DOWNSTREAM_PIPELINE_ENABLED if enabled is None else enabled
        self.base_url = (settings.DOWNSTREAM_PIPELINE_URL if base_url is None else base_url).strip().rstrip("/")
        self.events_path = self._normalize_path(
            settings.DOWNSTREAM_PIPELINE_EVENTS_PATH if events_path is None else events_path
        )
        self.auth_token = settings.DOWNSTREAM_PIPELINE_AUTH_TOKEN if auth_token is None else auth_token
        self.timeout = settings.DOWNSTREAM_PIPELINE_TIMEOUT_SECONDS if timeout is None else timeout

    def dispatch_event(self, event: OpsEvent) -> bool:
        return self.dispatch_event_payload(build_downstream_event_payload(event))

    def dispatch_event_payload(self, payload: Dict[str, Any]) -> bool:
        if not self.enabled or not self.base_url:
            return False

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout, headers=headers) as client:
                response = client.post(self.events_path, json=payload)
        except httpx.TimeoutException:
            logger.warning("Downstream pipeline dispatch timed out for %s", payload.get("event_id"))
            return False
        except httpx.RequestError as exc:
            logger.warning("Downstream pipeline dispatch failed for %s: %s", payload.get("event_id"), exc)
            return False

        if response.status_code >= 400:
            logger.warning(
                "Downstream pipeline returned %s for %s: %s",
                response.status_code,
                payload.get("event_id"),
                response.text,
            )
            return False

        return True

    def _normalize_path(self, path: str) -> str:
        normalized = path.strip() or "/events"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        return normalized


def _isoformat(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None
