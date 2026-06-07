from app.providers.base import SearchProvider


class GDAISearchProvider(SearchProvider):

    async def search(
        self,
        query_text: str,
        tenant=None,
        limit: int = 10,
        offset: int = 0,
        filters=None,
        sort=None,
    ):
        pass
