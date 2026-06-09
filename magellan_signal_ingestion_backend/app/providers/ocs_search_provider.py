import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.providers.base import MalformedProviderResponse, SearchProvider


class OCSSearchProvider(SearchProvider):

    async def search(
        self,
        query_text: str,
        tenant: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ):
        tenant_name = tenant or settings.OCS_TENANT
        path = self._normalize_path(settings.OCS_SEARCH_PATH_TEMPLATE.format(tenant=tenant_name))
        body = {
            "q": query_text,
            "limit": limit,
            "offset": offset,
            "filters": filters or {},
        }
        if sort:
            body["sort"] = sort

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if settings.OCS_AUTH:
            headers["Authorization"] = f"Basic {settings.OCS_AUTH}"

        start_time = time.time()
        try:
            async with httpx.AsyncClient(
                base_url=settings.OCS_SEARCH_URL.rstrip("/"),
                timeout=settings.REQUEST_TIMEOUT_SECONDS,
            ) as client:
                response = await client.post(path, json=body, headers=headers)
        except httpx.TimeoutException:
            return self._error_result(
                query_text=query_text,
                tenant=tenant_name,
                status_code=0,
                latency_ms=int((time.time() - start_time) * 1000),
                error_type="timeout",
            )
        except httpx.RequestError as exc:
            return self._error_result(
                query_text=query_text,
                tenant=tenant_name,
                status_code=0,
                latency_ms=int((time.time() - start_time) * 1000),
                error_type="provider_error",
                response_payload={"message": str(exc)},
            )

        latency_ms = int((time.time() - start_time) * 1000)

        if response.status_code >= 400:
            return self._error_result(
                query_text=query_text,
                tenant=tenant_name,
                status_code=response.status_code,
                latency_ms=latency_ms,
                error_type="client_error" if response.status_code < 500 else "provider_error",
                response_payload=self._safe_response_payload(response),
            )

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise MalformedProviderResponse("OCS response was not valid JSON") from exc

        if not isinstance(response_payload, dict) or not isinstance(response_payload.get("slices"), list):
            raise MalformedProviderResponse("OCS response did not include a valid slices array")

        result_count = self._result_count(response_payload)
        return {
            "provider": "ocs",
            "tenant": tenant_name,
            "query_text": query_text,
            "status_code": response.status_code,
            "success": True,
            "latency_ms": int(response_payload.get("tookInMillis") or latency_ms),
            "result_count": result_count,
            "top_product_ids": self._top_product_ids(response_payload),
            "response_payload": response_payload,
            "metadata": response_payload.get("meta") or {},
        }

    def _error_result(
        self,
        query_text: str,
        tenant: str,
        status_code: int,
        latency_ms: int,
        error_type: str,
        response_payload: Optional[Dict[str, Any]] = None,
    ):
        return {
            "provider": "ocs",
            "tenant": tenant,
            "query_text": query_text,
            "status_code": status_code,
            "success": False,
            "latency_ms": latency_ms,
            "result_count": 0,
            "top_product_ids": [],
            "response_payload": response_payload or {},
            "metadata": {},
            "error_type": error_type,
        }

    def _safe_response_payload(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            payload = response.json()
            return payload if isinstance(payload, dict) else {"payload": payload}
        except ValueError:
            return {"message": response.text}

    def _normalize_path(self, path: str) -> str:
        return path if path.startswith("/") else f"/{path}"

    def _result_count(self, response_payload: Dict[str, Any]) -> int:
        total = 0
        for result_slice in response_payload.get("slices", []):
            total += int(result_slice.get("matchCount") or 0)
        return total

    def _top_product_ids(self, response_payload: Dict[str, Any]) -> List[str]:
        product_ids: List[str] = []
        for result_slice in response_payload.get("slices", []):
            for hit in result_slice.get("hits") or []:
                document = hit.get("document") or {}
                data = document.get("data") or {}
                product_id = document.get("id") or data.get("product_id")
                if product_id is not None:
                    product_ids.append(str(product_id))
                if len(product_ids) == 10:
                    return product_ids
        return product_ids
