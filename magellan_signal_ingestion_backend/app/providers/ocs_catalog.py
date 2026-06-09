from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.utils.diff_utils import REQUIRED_ATTRIBUTES


class OCSClientError(Exception):

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class OCSCatalogClient:

    def __init__(
        self,
        base_url: Optional[str] = None,
        tenant: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OCS_SEARCH_URL).rstrip("/")
        self.tenant = tenant or settings.OCS_TENANT
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=settings.REQUEST_TIMEOUT_SECONDS if timeout is None else timeout,
            headers=self._headers(),
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "OCSCatalogClient":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        response = self._request(
            "GET",
            self._path(settings.OCS_GET_PRODUCT_PATH_TEMPLATE, product_id=product_id),
        )
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise OCSClientError(
                f"OCS get_product failed for {product_id}: {response.status_code}",
                response.status_code,
            )
        payload = response.json()
        return self._normalize_product(payload, product_id) if isinstance(payload, dict) else {"id": product_id, "payload": payload}

    def add_product(self, product: Dict[str, Any]) -> bool:
        document = self._to_ocs_document(product)
        response = self._request(
            "PUT",
            self._path(settings.OCS_INDEX_UPDATE_PATH_TEMPLATE),
            params={"langCode": "en"},
            json=[document],
        )
        return self._success(response, {200, 201, 204})

    def update_product(self, product_id: str, fields: Dict[str, Any]) -> bool:
        document = self._fields_to_ocs_document(product_id, fields)
        response = self._request("PATCH", self._path(settings.OCS_INDEX_UPDATE_PATH_TEMPLATE), json=[document])
        return self._success(response, {200, 201, 204})

    def delete_product(self, product_id: str) -> bool:
        response = self._request(
            "DELETE",
            self._path(settings.OCS_INDEX_UPDATE_PATH_TEMPLATE),
            params=[("id[]", product_id)],
        )
        return self._success(response, {200, 204})

    def flush_config(self) -> bool:
        response = self._request("GET", self._path(settings.OCS_FLUSH_CONFIG_PATH_TEMPLATE))
        return self._success(response, {200})

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if settings.OCS_AUTH:
            headers["Authorization"] = f"Basic {settings.OCS_AUTH}"
        return headers

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            response = self.client.request(method, url, **kwargs)
        except httpx.TimeoutException as exc:
            raise OCSClientError(f"OCS request timed out: {method} {url}") from exc
        except httpx.RequestError as exc:
            raise OCSClientError(f"OCS request failed: {method} {url}: {exc}") from exc

        if response.status_code >= 500:
            raise OCSClientError(
                f"OCS server error for {method} {url}: {response.status_code}",
                response.status_code,
            )
        return response

    def _path(self, template: str, **values: Any) -> str:
        path = template.format(tenant=self.tenant, **values)
        return path if path.startswith("/") else f"/{path}"

    def _success(self, response: httpx.Response, success_codes: set[int]) -> bool:
        return response.status_code in success_codes

    def _to_ocs_document(self, product: Dict[str, Any]) -> Dict[str, Any]:
        if "data" in product and "id" in product:
            return product

        product_id = str(product.get("id") or product.get("product_id"))
        data: Dict[str, Any] = {}
        for key, value in product.items():
            if key in {"id", "product_id", "attributes"}:
                continue
            if self._is_supported_data_value(value):
                data[key] = value

        attributes = product.get("attributes") or {}
        if isinstance(attributes, dict):
            for key, value in attributes.items():
                if self._is_supported_data_value(value):
                    data[key] = value

        if data.get("stock") == 0:
            data["inventory_status"] = "out_of_stock"
        elif "stock" in data:
            data["inventory_status"] = "in_stock"

        return {"id": product_id, "data": data}

    def _fields_to_ocs_document(self, product_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for key, value in fields.items():
            if key == "attributes" and isinstance(value, dict):
                data.update(value)
            elif key != "id":
                data[key] = value

        if data.get("stock") == 0:
            data["inventory_status"] = "out_of_stock"
        elif "stock" in data:
            data["inventory_status"] = "in_stock"

        return {"id": product_id, "data": data}

    def _normalize_product(self, payload: Dict[str, Any], fallback_id: str) -> Dict[str, Any]:
        if "data" not in payload:
            return payload

        data = payload.get("data") or {}
        product = dict(data)
        product["id"] = str(payload.get("id") or fallback_id)
        category = str(product.get("category") or "").lower()
        required_attributes = REQUIRED_ATTRIBUTES.get(category, [])
        if required_attributes:
            product["attributes"] = {attribute: data.get(attribute) for attribute in required_attributes}
        if "stock" in product:
            product["stock"] = int(product["stock"])
        return product

    def _is_supported_data_value(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, (str, int, float, bool)):
            return True
        if isinstance(value, list):
            return all(isinstance(item, (str, int, float, bool)) or item is None for item in value)
        return False
