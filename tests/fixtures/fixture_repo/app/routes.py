"""API Route Handlers."""

from typing import Dict, Any
import app.auth
from app.auth import authenticate_user
from app.services import user_service_lookup, process_payment


def login_route(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """API Endpoint: /api/login handling user authentication."""
    username = request_data.get("username", "")
    password = request_data.get("password", "")
    user = authenticate_user(username, password)
    if user:
        return {"status": 200, "user": user, "token": user.get("token")}
    return {"status": 401, "error": "Invalid credentials"}


def user_profile_route(token: str) -> Dict[str, Any]:
    """API Endpoint: /api/user profile lookup."""
    user = user_service_lookup(token)
    if user:
        return {"status": 200, "user": user}
    return {"status": 404, "error": "User not found"}


def payment_route(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """API Endpoint: /api/pay processing payments."""
    token = request_data.get("token", "")
    amount = float(request_data.get("amount", 0.0))
    result = process_payment(token, amount)
    return {"status": 200 if result["success"] else 400, "result": result}
