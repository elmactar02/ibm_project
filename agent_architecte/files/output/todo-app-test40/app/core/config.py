from __future__ import annotations

from pathlib import Path
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Environment variables:
        APP_SECRET_KEY: Secret key used for JWT signing and other cryptographic
            operations. Must be a non‑empty string.
        DATABASE_URL: SQLAlchemy database URL. Example formats:
            - sqlite:///./test.db
            - postgresql+psycopg2://user:password@host:port/dbname

    The values are read from a ``.env`` file located in the project root if
    present. The file must contain ``APP_SECRET_KEY`` and ``DATABASE_URL`` keys.

    Attributes
    ----------
    app_secret_key: str
        Secret key for cryptographic operations.
    database_url: str
        SQLAlchemy connection string.
    """

    app_secret_key: str = Field(..., env="APP_SECRET_KEY")
    database_url: str = Field(..., env="DATABASE_URL")

    @validator("app_secret_key")
    def _validate_secret_key(cls, value: str) -> str:
        """Ensure the secret key is not empty.

        Args:
            value: The raw secret key string.

        Returns:
            The validated secret key.

        Raises:
            ValueError: If the secret key is an empty string.
        """
        if not value.strip():
            raise ValueError("APP_SECRET_KEY cannot be empty")
        return value

    class Config:
        """Pydantic configuration for Settings."""

        env_file = str(Path(__file__).resolve().parents[2] / ".env")
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Create and return a Settings instance.

    Returns:
        Settings: The application configuration loaded from the environment.
    """
    return Settings()