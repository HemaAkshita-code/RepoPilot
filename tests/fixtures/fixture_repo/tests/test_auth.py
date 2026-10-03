"""Tests for auth module."""

from app.auth import authenticate_user, create_access_token, verify_token


def test_authentication():
    user = authenticate_user("admin", "secret")
    assert user is not None
    assert user["id"] == 1


def test_token_verification():
    token = create_access_token(42)
    user_id = verify_token(token)
    assert user_id == 42
