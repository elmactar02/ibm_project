from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes
    ----------
    db_api_url : str
        Base URL of the remote database API. Defaults to
        ``http://localhost:8003`` if not overridden by the
        ``DB_API_URL`` environment variable.

    Notes
    -----
    The settings are read from a ``.env`` file located at the project root.
    No other environment variables are required for this proxy application.
    """

    db_api_url: str = Field(
        default="http://localhost:8003",
        description="Base URL of the remote database API",
    )

    model_config = SettingsConfigDict(env_file=".env")
