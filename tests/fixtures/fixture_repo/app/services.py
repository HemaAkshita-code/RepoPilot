"""Business services layer."""

from typing import Optional, Dict, Any
import app.auth
from app.auth import verify_token
from app.database import get_user_by_id


def user_service_lookup(token: str) -> Optional[Dict[str, Any]]:
    """Retrieve user details using authentication token."""
    user_id = verify_token(token)
    if user_id is not None:
        return get_user_by_id(user_id)
    return None


def process_payment(token: str, amount: float) -> Dict[str, Any]:
    """Process customer payment after verifying user identity."""
    user = user_service_lookup(token)
    if not user:
        return {"success": False, "error": "Unauthorized"}
    return {"success": True, "amount": amount, "user_id": user["id"]}
