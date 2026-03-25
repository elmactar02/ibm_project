from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes
    ----------
    db_api_url : str
        Base URL of the remote database API. Defaults to
        ``http://localhost:8003`` if not specified in the environment.
    """

    db_api_url: str = Field(
        default="http://localhost:8003",
        env="DB_API_URL",
        description="Base URL of the remote database API",
    )

    model_config = SettingsConfigDict(env_file=".env")
    
__all__ = ["Settings"]