
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application security
    secret_key: str = ""
    session_secret: str = ""

    # JWT configuration
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Cookie configuration
    cookie_secure: bool = False

    # Google OAuth configuration
    google_client_id_1: str = ""
    google_client_secret_1: str = ""
    google_redirect_uri: str = (
        "http://localhost:8000/google/callback"
    )

    # Frontend configuration
    frontend_url: str = "http://localhost:5173"

    # AI and integrations
    openai_api_key: str = ""
    composio_api_key: str = ""
    model: str = "gpt-5-nano"
    mcp_require_approval: str = "never"

    # Database
    database_url: str = "sqlite+aiosqlite:///./authspace.db"

    # CORS
    cors_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    # Request validation
    max_question_length: int = 8000

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
