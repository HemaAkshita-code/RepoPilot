"""Configuration module for RepoPilot backend."""

import os
from dataclasses import dataclass
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class ConfigurationError(Exception):
    """Raised when required configuration values are missing or invalid."""
    pass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""
    api_key: str
    model: str


def get_settings() -> Settings:
    """Load and validate configuration from environment variables.

    Reads:
        GEMMA_API_KEY: Secret API key for Google GenAI / Gemma API.
        GEMMA_MODEL: Model identifier (e.g., 'gemma-4-31b-it').

    Returns:
        Settings: Validated configuration object.

    Raises:
        ConfigurationError: If any required configuration variables are missing.
    """
    api_key = os.environ.get("GEMMA_API_KEY", "").strip()
    model = os.environ.get("GEMMA_MODEL", "").strip()

    missing = []
    if not api_key:
        missing.append("GEMMA_API_KEY")
    if not model:
        missing.append("GEMMA_MODEL")

    if missing:
        raise ConfigurationError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Please ensure they are defined in your environment or .env file."
        )

    return Settings(api_key=api_key, model=model)
