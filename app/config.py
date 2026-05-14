from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://vkmon:vkmon@localhost:5433/vkmon"
    vk_service_token: str = ""
    vk_api_version: str = "5.199"
    session_secret_key: str = "dev-secret"
    bootstrap_admin_login: str = "admin"
    bootstrap_admin_password: str = "admin"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
