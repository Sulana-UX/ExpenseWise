from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application and Security Configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = Field(default="development", description="Application runtime environment")
    DATABASE_URL: str = Field(
        default="sqlite:///./expense_tracker.db",
        description="SQLAlchemy database connection string",
    )
    JWT_SECRET_KEY: str = Field(
        default="dev_insecure_jwt_secret_key_for_local_testing_only_replace_in_production_32chars",
        description="Cryptographic secret key for signing JWT tokens",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="Access token lifespan in minutes",
    )
    BACKEND_HOST: str = Field(default="127.0.0.1", description="Host to bind server")
    BACKEND_PORT: int = Field(default=8000, description="Port to bind server")


settings = Settings()
