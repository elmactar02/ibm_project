from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    The settings are read from a ``.env`` file located at the project root.
    Only two variables are required:

    - ``APP_SECRET_KEY``: Secret key used for JWT signing and other cryptographic
      operations.
    - ``DATABASE_URL``: SQLAlchemy database connection URL.

    Attributes:
        app_secret_key: Secret key for cryptographic operations.
        database_url: Database connection string compatible with SQLAlchemy.

    Raises:
        ValidationError: If any required environment variable is missing or
        fails validation.
    """

    app_secret_key: str = Field(..., env="APP_SECRET_KEY")
    database_url: str = Field(..., env="DATABASE_URL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")