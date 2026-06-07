from app.core.config import settings

from app.providers.meilisearch_provider import MeilisearchProvider
from app.providers.gd_ai_search_provider import GDAISearchProvider
from app.providers.ocs_search_provider import OCSSearchProvider


def get_search_provider():

    provider_name = settings.SEARCH_PROVIDER.lower()

    if provider_name == "ocs":
        return OCSSearchProvider()

    if provider_name == "gd_ai_search":
        return GDAISearchProvider()

    return MeilisearchProvider()
