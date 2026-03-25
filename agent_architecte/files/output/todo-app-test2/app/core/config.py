from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Attributes:
        APP_SECRET_KEY: Secret key used for JWT signing.
        DATABASE_URL: Database connection URL.
    """

    APP_SECRET_KEY: str = Field(..., env="APP_SECRET_KEY")
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    @field_validator("APP_SECRET_KEY", "DATABASE_URL")
    @classmethod
    def _strip_and_validate(cls, value: str) -> str:
        """Strip whitespace and ensure the value is not empty.

        Args:
            value: Raw string from the environment.

        Returns:
            The stripped string.

        Raises:
            ValueError: If the resulting string is empty.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("environment variable must not be empty")
        return stripped

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


__all__ = ["Settings"]