import time
from typing import Any, Dict, Optional

import meilisearch

from app.providers.base import SearchProvider
from app.core.config import settings

client = meilisearch.Client(settings.MEILISEARCH_URL)


class MeilisearchProvider(SearchProvider):

    async def search(
        self,
        query_text: str,
        tenant: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ):

        start_time = time.time()

        response = client.index("products").search(
            query_text,
            {
                "limit": limit,
                "offset": offset,
            }
        )

        latency_ms = int((time.time() - start_time) * 1000)

        hits = response.get("hits", [])

        return {

            "provider": "meilisearch",

            "tenant": tenant,

            "query_text": query_text,

            "status_code": 200,

            "success": True,

            "latency_ms": latency_ms,

            "result_count": len(hits),

            "top_product_ids": [
                item["product_id"]
                for item in hits[:10]
            ],

            "response_payload": response
        }
