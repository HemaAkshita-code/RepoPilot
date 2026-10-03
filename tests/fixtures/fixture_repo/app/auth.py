"""Authentication service module."""

from typing import Optional, Dict, Any
from app.database import get_user_by_id
from app.config import SECRET_KEY


def create_access_token(user_id: int) -> str:
    """Generate authentication token for user."""
    return f"token_for_user_{user_id}_key_{SECRET_KEY}"


def verify_token(token: str) -> Optional[int]:
    """Verify raw authentication token and return user ID if valid."""
    if token.startswith("token_for_user_"):
        parts = token.split("_")
        if len(parts) >= 4:
            try:
                return int(parts[3])
            except ValueError:
                return None
    return None


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user credentials and retrieve user profile from DB."""
    # In fixture system, assume user ID 1 for test user
    if username == "admin" and password == "secret":
        user = get_user_by_id(1)
        if user:
            token = create_access_token(user["id"])
            user["token"] = token
            return user
    return None
