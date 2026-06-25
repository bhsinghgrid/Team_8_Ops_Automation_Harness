from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    SEARCH_PROVIDER: str = "ocs"

    GD_AI_SEARCH_URL: str = ""
    GD_AI_SEARCH_API_KEY: str = ""

    OCS_SEARCH_URL: str = "http://127.0.0.1:8534"
    OCS_TENANT: str = "ocs_example"
    OCS_AUTH: str = ""
    REQUEST_TIMEOUT_SECONDS: float = 5.0

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/magellan"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
