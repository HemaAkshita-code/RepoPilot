"""Sample application configuration."""

DATABASE_URL = "sqlite:///app.db"
SECRET_KEY = "secret-key-val"
REDIS_HOST = "localhost"
REDIS_PORT = 6379


def get_db_url() -> str:
    """Return database URL."""
    return DATABASE_URL
