from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from filelock import FileLock

from app.schemas.signal_schema import CatalogDiffRequest
from app.utils.diff_utils import REQUIRED_ATTRIBUTES, get_by_dot_path

CATEGORY_ORDER = ["footwear", "bags", "outerwear", "electronics", "camping"]


class ProductStateError(ValueError):
    pass


class ProductStateManager:

    def __init__(self, mock_data_root: Optional[Path] = None):
        self.mock_data_root = mock_data_root or Path(__file__).resolve().parents[2] / "mock-data"
        self.products_root = self.mock_data_root / "products"
        self.index_path = self.mock_data_root / "index" / "product_index.json"
        self.lock = FileLock(str(self.mock_data_root / "catalog_state.lock"))

    def apply_diff(self, signal: CatalogDiffRequest) -> Optional[Dict[str, Any]]:
        operation = signal.operation.upper()
        with self.lock:
            product_files = self._read_product_files()
            location = self._find_product(product_files, signal.product_id)

            if operation == "INSERT":
                product = self._product_from_after(signal)
                self._upsert_product(product_files, product, location)
                self._write_state(product_files)
                return deepcopy(product)

            if operation == "UPDATE":
                if location is None:
                    raise ProductStateError(f"Product {signal.product_id} was not found")
                if not signal.after:
                    raise ProductStateError(f"UPDATE for product {signal.product_id} requires after")

                category, index, existing = location
                updated_product = deepcopy(existing)
                fields = signal.changed_fields or list(signal.after.keys())
                for field in fields:
                    self._set_dot_path(updated_product, field, self._value_from_after(signal.after, field))
                self._upsert_product(product_files, updated_product, (category, index, existing))
                self._write_state(product_files)
                return deepcopy(updated_product)

            if operation == "DELETE":
                if location is None:
                    raise ProductStateError(f"Product {signal.product_id} was not found")
                category, index, existing = location
                product_files[category].setdefault("products", []).pop(index)
                self._sort_products(product_files[category])
                self._write_state(product_files)
                return deepcopy(existing)

            raise ProductStateError(f"Unsupported catalog operation {signal.operation}")

    def _product_from_after(self, signal: CatalogDiffRequest) -> Dict[str, Any]:
        if not signal.after:
            raise ProductStateError(f"INSERT for product {signal.product_id} requires after")
        product = self._normalize_product_payload(signal.after)
        product["id"] = signal.product_id
        if not product.get("category"):
            raise ProductStateError(f"Product {signal.product_id} requires category")
        return product

    def _normalize_product_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(payload.get("data"), dict):
            data = dict(payload["data"])
            product = data
            product["id"] = payload.get("id") or data.get("id")
            category = str(product.get("category") or "").lower()
            required = REQUIRED_ATTRIBUTES.get(category, [])
            if required and not isinstance(product.get("attributes"), dict):
                product["attributes"] = {attribute: data.get(attribute) for attribute in required}
            return product
        return deepcopy(payload)

    def _upsert_product(
        self,
        product_files: Dict[str, Dict[str, Any]],
        product: Dict[str, Any],
        location: Optional[Tuple[str, int, Dict[str, Any]]],
    ) -> None:
        category = self._category_for_product(product)
        if category not in product_files:
            raise ProductStateError(f"Unsupported product category {category}")

        if location is not None:
            old_category, index, _existing = location
            if old_category == category:
                product_files[category].setdefault("products", [])[index] = deepcopy(product)
            else:
                product_files[old_category].setdefault("products", []).pop(index)
                product_files[category].setdefault("products", []).append(deepcopy(product))
        else:
            product_files[category].setdefault("products", []).append(deepcopy(product))

        for payload in product_files.values():
            self._sort_products(payload)

    def _category_for_product(self, product: Dict[str, Any]) -> str:
        return str(product.get("category") or "").lower()

    def _value_from_after(self, after: Dict[str, Any], field: str) -> Any:
        if field in after:
            return after[field]
        return get_by_dot_path(after, field)

    def _set_dot_path(self, payload: Dict[str, Any], path: str, value: Any) -> None:
        parts = path.split(".")
        current = payload
        for part in parts[:-1]:
            next_value = current.get(part)
            if not isinstance(next_value, dict):
                next_value = {}
                current[part] = next_value
            current = next_value
        current[parts[-1]] = value

    def _read_product_files(self) -> Dict[str, Dict[str, Any]]:
        product_files: Dict[str, Dict[str, Any]] = {}
        for category in CATEGORY_ORDER:
            path = self.products_root / f"{category}.json"
            if path.exists():
                product_files[category] = self._read_json(path)
        for path in sorted(self.products_root.glob("*.json")):
            category = path.stem
            if category not in product_files:
                product_files[category] = self._read_json(path)
        return product_files

    def _find_product(
        self,
        product_files: Dict[str, Dict[str, Any]],
        product_id: str,
    ) -> Optional[Tuple[str, int, Dict[str, Any]]]:
        for category, payload in product_files.items():
            for index, product in enumerate(payload.get("products", [])):
                if product.get("id") == product_id:
                    return category, index, deepcopy(product)
        return None

    def _write_state(self, product_files: Dict[str, Dict[str, Any]]) -> None:
        for category, payload in product_files.items():
            self._write_json(self.products_root / f"{category}.json", payload)
        self._write_json(self.index_path, self._build_index(product_files))

    def _build_index(self, product_files: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        products = [
            {
                "id": product["id"],
                "category": product["category"],
                "stock": product["stock"],
                "data_quality": product["data_quality"],
            }
            for category in self._ordered_categories(product_files)
            for product in product_files[category].get("products", [])
        ]
        return {
            "description": "Flat index of all product IDs for quick lookup",
            "total": len(products),
            "products": products,
            "oos_products": [product["id"] for product in products if product["stock"] == 0],
            "low_stock_products": [product["id"] for product in products if 1 <= product["stock"] <= 10],
            "incomplete_products": [product["id"] for product in products if product["data_quality"] == "incomplete"],
            "poor_products": [product["id"] for product in products if product["data_quality"] == "poor"],
            "new_arrivals": [product["id"] for product in products if product["data_quality"] == "new_arrival"],
        }

    def _ordered_categories(self, product_files: Dict[str, Dict[str, Any]]) -> list[str]:
        ordered = [category for category in CATEGORY_ORDER if category in product_files]
        ordered.extend(sorted(category for category in product_files if category not in CATEGORY_ORDER))
        return ordered

    def _sort_products(self, payload: Dict[str, Any]) -> None:
        payload.setdefault("products", []).sort(key=lambda product: str(product.get("id") or ""))

    def _read_json(self, path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temp_path.replace(path)
