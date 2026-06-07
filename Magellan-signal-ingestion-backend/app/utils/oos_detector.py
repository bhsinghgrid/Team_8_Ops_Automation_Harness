from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.providers.ocs_catalog import OCSCatalogClient, OCSClientError

logger = logging.getLogger(__name__)


def detect_oos_conflicts(target_products: List[str], ocs_client: OCSCatalogClient) -> List[Dict[str, Any]]:
    conflicts: List[Dict[str, Any]] = []
    for product_id in target_products:
        try:
            product = ocs_client.get_product(product_id)
        except OCSClientError as error:
            logger.warning("Could not verify stock for %s: %s", product_id, error)
            continue

        if product is None:
            continue

        stock = _product_value(product, "stock", default=1)
        inventory_status = _product_value(product, "inventory_status")
        if stock == 0 or str(inventory_status).lower() == "out_of_stock":
            conflicts.append(
                {
                    "product_id": product_id,
                    "title": _product_value(product, "title"),
                    "stock": stock if stock is not None else 0,
                    "conflict": "rule targets out-of-stock product",
                }
            )
    return conflicts


def _product_value(product: Dict[str, Any], key: str, default: Any = None) -> Any:
    if key in product:
        return product.get(key, default)
    data = product.get("data")
    if isinstance(data, dict):
        return data.get(key, default)
    document = product.get("document")
    if isinstance(document, dict):
        document_data = document.get("data")
        if isinstance(document_data, dict):
            return document_data.get(key, default)
        return document.get(key, default)
    return default
