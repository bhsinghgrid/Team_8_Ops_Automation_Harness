from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class CatalogProduct:
    """
    Canonical catalog product record shared across all repository implementations.
    """
    product_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    in_stock: Optional[bool] = None
    # Add the fields from the original model with defaults to avoid breaking other tools
    sku: Optional[str] = None
    brand: Optional[str] = None
    waterproof_flag: Optional[bool] = None
    terrain_type: Optional[str] = None
    status: Optional[str] = None
    updated_at: Optional[str] = None
