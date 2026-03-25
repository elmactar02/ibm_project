from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Attributes:
        db_api_url: Base URL of the remote database HTTP API.
    """

    db_api_url: str = Field(
        default="http://localhost:8003",
        description="Base URL for the remote DB API",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("db_api_url")
    @classmethod
    def validate_db_api_url(cls, value: str) -> str:
        """Validate that ``db_api_url`` is a proper HTTP/HTTPS URL.

        Args:
            value: The URL string to validate.

        Returns:
            The original URL if it passes validation.

        Raises:
            ValueError: If the URL does not start with ``http://`` or ``https://``.
        """
        if not value.startswith(("http://", "https://")):
            raise ValueError("db_api_url must start with http:// or https://")
        return value