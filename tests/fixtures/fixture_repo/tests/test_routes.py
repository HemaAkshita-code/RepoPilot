"""Tests for routes module."""

from app.routes import login_route, user_profile_route


def test_login_flow():
    response = login_route({"username": "admin", "password": "secret"})
    assert response["status"] == 200
    token = response["token"]
    
    profile_resp = user_profile_route(token)
    assert profile_resp["status"] == 200
