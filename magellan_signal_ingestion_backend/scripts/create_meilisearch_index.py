import meilisearch
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402

client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY or None)

client.create_index(
    uid="products",
    options={
        "primaryKey": "product_id"
    }
)

index = client.index("products")

index.update_searchable_attributes([
    "title",
    "description",
    "attributes",
    "brand",
    "category"
])

index.update_filterable_attributes([
    "category",
    "brand",
    "stock",
    "quality_flags"
])

print("Products index created")
