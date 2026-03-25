from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Attributes:
        app_secret_key: Secret key used for JWT signing and other cryptographic
            operations. Must be provided via the ``APP_SECRET_KEY`` environment
            variable.
        database_url: SQLAlchemy database connection URL. Must be provided via the
            ``DATABASE_URL`` environment variable.

    Raises:
        ValueError: If either ``app_secret_key`` or ``database_url`` is empty
            after stripping whitespace.
    """

    app_secret_key: str = Field(..., env="APP_SECRET_KEY")
    database_url: str = Field(..., env="DATABASE_URL")

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("app_secret_key", "database_url", mode="before")
    @classmethod
    def _strip_and_validate(cls, value: str) -> str:
        """Strip surrounding whitespace and ensure the value is not empty.

        Args:
            value: Raw string value from the environment.

        Returns:
            The stripped string.

        Raises:
            ValueError: If the stripped value is empty.
        """
        if not isinstance(value, str):
            raise TypeError("Configuration values must be strings")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Configuration value cannot be empty")
        return stripped

__all__ = ["Settings"]