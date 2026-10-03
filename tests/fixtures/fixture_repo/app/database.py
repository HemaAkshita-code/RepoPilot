"""Database persistence layer."""

from typing import Optional, Dict, Any
from app.config import DATABASE_URL


def query_db(sql: str, params: tuple = ()) -> list:
    """Execute raw database query using DATABASE_URL connection."""
    # Simulated database query execution
    print(f"Connecting to {DATABASE_URL}")
    return [{"id": 1, "username": "admin", "is_active": True}]


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve user record from database by ID."""
    results = query_db("SELECT * FROM users WHERE id = ?", (user_id,))
    if results:
        return results[0]
    return None
