from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(alias="BOT_USERNAME")
    bot_webhook_secret: str = Field(alias="BOT_WEBHOOK_SECRET")
    public_webhook_url: str = Field(alias="PUBLIC_WEBHOOK_URL")

    mongodb_uri: str = Field(alias="MONGODB_URI")
    mongodb_db: str = Field(alias="MONGODB_DB", default="telegram_premium_bot")
    redis_url: str = Field(alias="REDIS_URL")

    jwt_secret: str = Field(alias="JWT_SECRET")
    owner_username: str = Field(alias="OWNER_USERNAME")
    owner_user_id: int = Field(alias="OWNER_USER_ID")
    updates_channel: str = Field(alias="UPDATES_CHANNEL")
    frontend_url: str = Field(alias="FRONTEND_URL")
    cors_origins: str = Field(alias="CORS_ORIGINS", default="")

    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 60 * 60 * 24 * 7
    cleanup_interval_seconds: int = 300
    spam_window_seconds: int = 300

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
