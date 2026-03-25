from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings.

    Attributes
    ----------
    APP_SECRET_KEY : str
        Secret key used for signing JWT tokens.
    DB_API_URL : str
        Base URL of the remote database API. Defaults to
        ``http://localhost:8003`` if not provided in the environment.

    Notes
    -----
    Settings are loaded from a ``.env`` file located at the project root.
    """

    APP_SECRET_KEY: str
    DB_API_URL: str = "http://localhost:8003"

    model_config = SettingsConfigDict(env_file=".env")
    
    def __repr__(self) -> str:
        return (
            f"<Settings(APP_SECRET_KEY=***, DB_API_URL={self.DB_API_URL!r})>"
        )