"""Global settings and configuration for Reddit Analyzer."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="reddit_analyzer")
    postgres_password: str = Field(default="dev_password")
    postgres_db: str = Field(default="reddit_analyzer")

    # Anthropic API
    anthropic_api_key: str = Field(default="")

    # Reddit API
    reddit_client_id: str = Field(default="")
    reddit_client_secret: str = Field(default="")
    reddit_user_agent: str = Field(default="RedditAnalyzer/2.0 (by /u/RedditAnalyzerBot)")

    # Application Settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    posts_limit: int = Field(default=100)
    comments_limit: int = Field(default=50)
    rate_limit_requests_per_minute: int = Field(default=30)

    # Model Configuration
    model_fast: str = Field(default="claude-haiku-4-5-20250514")
    model_balanced: str = Field(default="claude-sonnet-4-20250514")
    model_powerful: str = Field(default="claude-sonnet-4-20250514")

    @property
    def database_url(self) -> str:
        """Construct the database URL from components."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def async_database_url(self) -> str:
        """Construct the async database URL from components."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Model mapping for different task types
MODEL_MAPPING = {
    "sentiment_analysis": "model_fast",
    "pain_point_analysis": "model_fast",
    "tone_analysis": "model_fast",
    "promotion_analysis": "model_fast",
    "persona_generation": "model_fast",
    "insight_generation": "model_balanced",
    "report_generation": "model_balanced",
}


def get_model_for_task(task: str) -> str:
    """Get the appropriate model for a given task."""
    settings = get_settings()
    model_attr = MODEL_MAPPING.get(task, "model_fast")
    return getattr(settings, model_attr)
