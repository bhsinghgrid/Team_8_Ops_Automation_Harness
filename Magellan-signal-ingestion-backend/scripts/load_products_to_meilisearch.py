#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import meilisearch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402
from app.db.database import SessionLocal, init_db  # noqa: E402
from app.providers.product_state_manager import ProductStateManager  # noqa: E402


def run() -> None:
    init_db()
    client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY)
    index = client.index("products")

    with SessionLocal() as db:
        products = ProductStateManager(db).list_products()

    index.add_documents(products)
    print(f"Loaded {len(products)} products into Meilisearch")


if __name__ == "__main__":
    run()
