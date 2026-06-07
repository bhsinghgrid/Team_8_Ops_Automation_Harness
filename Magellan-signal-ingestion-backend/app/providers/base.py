from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class SearchProvider(ABC):

    @abstractmethod
    async def search(
        self,
        query_text: str,
        tenant: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ):
        pass


class MalformedProviderResponse(Exception):

    pass
