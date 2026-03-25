from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from a ``.env`` file.

    Attributes
    ----------
    db_api_url: str
        Base URL of the remote database API. Defaults to ``http://localhost:8003``.
    """

    db_api_url: str = Field(
        default="http://localhost:8003",
        description="Base URL of the remote database API",
    )

    @field_validator("db_api_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        """Remove a trailing slash to ensure consistent URL concatenation.

        Args:
            value: The raw URL string from the environment.

        Returns:
            The URL without a trailing slash.
        """
        return value.rstrip("/")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")