from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    MAGELLAN_API_URL: str = "http://127.0.0.1:8000"

    SEARCH_PROVIDER: str = "ocs"

    MEILISEARCH_URL: str = "http://localhost:7700"
    MEILISEARCH_API_KEY: str = ""

    GD_AI_SEARCH_URL: str = ""
    GD_AI_SEARCH_API_KEY: str = ""

    OCS_SEARCH_URL: str = "http://127.0.0.1:8534"
    OCS_TENANT: str = "ocs_example"
    OCS_AUTH: str = ""
    OCS_SEARCH_PATH_TEMPLATE: str = "/search-api/v1/search/arranged/{tenant}"
    OCS_GET_PRODUCT_PATH_TEMPLATE: str = "/search-api/v1/doc/{tenant}/{product_id}"
    OCS_INDEX_UPDATE_PATH_TEMPLATE: str = "/indexer-api/v1/update/{tenant}"
    OCS_FLUSH_CONFIG_PATH_TEMPLATE: str = "/search-api/v1/flushConfig/{tenant}"
    REQUEST_TIMEOUT_SECONDS: float = 5.0

    DOWNSTREAM_PIPELINE_ENABLED: bool = False
    DOWNSTREAM_PIPELINE_URL: str = ""
    DOWNSTREAM_PIPELINE_EVENTS_PATH: str = "/events"
    DOWNSTREAM_PIPELINE_AUTH_TOKEN: str = ""
    DOWNSTREAM_PIPELINE_SOURCE: str = "magellan-signal-ingestion"
    DOWNSTREAM_PIPELINE_TIMEOUT_SECONDS: float = 5.0

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/magellan"
    ELASTICSEARCH_URL: str = "http://localhost:9200"


settings = Settings()
