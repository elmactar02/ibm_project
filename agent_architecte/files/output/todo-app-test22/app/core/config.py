from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from a .env file.

    Attributes
    ----------
    db_api_url: str
        Base URL of the remote database HTTP API. Defaults to
        ``http://localhost:8003`` and can be overridden via the
        ``DB_API_URL`` environment variable.

    Raises
    ------
    ValueError
        If ``db_api_url`` does not start with ``http://`` or ``https://``.
    """

    db_api_url: str = Field(default="http://localhost:8003", env="DB_API_URL")

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("db_api_url")
    @classmethod
    def validate_db_api_url(cls, value: str) -> str:
        """
        Ensure the provided API URL uses a supported scheme.

        Args
        ----
        value: str
            The URL to validate.

        Returns
        -------
        str
            The validated URL.

        Raises
        ------
        ValueError
            If the URL does not start with ``http://`` or ``https://``.
        """
        if not value.startswith(("http://", "https://")):
            raise ValueError("db_api_url must start with 'http://' or 'https://'")
        return value