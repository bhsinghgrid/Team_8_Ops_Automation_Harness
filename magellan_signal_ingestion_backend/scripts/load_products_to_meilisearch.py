import json
import sys
from pathlib import Path

import meilisearch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402

client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY or None)

index = client.index("products")

with open(
    "mock_data/products/products.json",
    "r"
) as file:

    products = json.load(file)

index.add_documents(products)

print("Products loaded")
