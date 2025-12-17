from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "CRM API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./crm.db"
    database_echo: bool = False

    # Security (for future JWT implementation)
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI / Email Intake
    ai_provider: str = "openai"  # "openai" or "anthropic"
    ai_model: str = "gpt-4o-mini"  # or "claude-3-5-sonnet-20241022"
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Webhook Secrets (for email providers)
    sendgrid_webhook_secret: str = ""  # Optional: custom header validation
    mailgun_webhook_secret: str = ""   # Required: Mailgun API key for signature validation
    generic_webhook_secret: str = ""    # Required: Token for X-Webhook-Token header

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
