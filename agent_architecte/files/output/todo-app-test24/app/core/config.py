from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from a ``.env`` file.

    Attributes
    ----------
    db_api_url: str
        Base URL of the remote database HTTP API. Defaults to
        ``http://localhost:8003`` and can be overridden via the
        ``DB_API_URL`` environment variable.

    Notes
    -----
    The settings are read exclusively from the ``.env`` file located in the
    project root. No other environment sources are consulted.
    """

    db_api_url: str = Field(
        default="http://localhost:8003",
        description="Base URL for the remote database HTTP API",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")