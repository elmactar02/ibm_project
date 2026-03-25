from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings.

    Attributes
    ----------
    db_api_url : str
        Base URL of the remote database API.  The value is read from the
        ``DB_API_URL`` environment variable.  If the variable is not set,
        the default value ``http://localhost:8003`` is used.

    Notes
    -----
    Settings are loaded from a ``.env`` file located in the project root.
    """

    db_api_url: str = "http://localhost:8003"

    model_config = SettingsConfigDict(env_file=".env")