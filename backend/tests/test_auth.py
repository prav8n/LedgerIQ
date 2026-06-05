"""Integration test for the auth flow: register -> login -> profile."""

from __future__ import annotations

API = "/api/v1/auth"


def test_register_login_profile(client):
    # Register (auto-login: returns tokens)
    reg = client.post(
        f"{API}/register",
        json={"email": "user@example.com", "password": "password123", "full_name": "Test"},
    )
    assert reg.status_code == 201
    body = reg.json()
    assert body["user"]["email"] == "user@example.com"
    assert body["tokens"]["access_token"]

    # Duplicate email is rejected
    dup = client.post(
        f"{API}/register", json={"email": "user@example.com", "password": "password123"}
    )
    assert dup.status_code == 409

    # Login with correct credentials
    login = client.post(
        f"{API}/login", json={"email": "user@example.com", "password": "password123"}
    )
    assert login.status_code == 200
    access = login.json()["tokens"]["access_token"]

    # Authenticated profile
    profile = client.get(f"{API}/profile", headers={"Authorization": f"Bearer {access}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == "user@example.com"

    # Wrong password -> 401
    bad = client.post(
        f"{API}/login", json={"email": "user@example.com", "password": "wrong-password"}
    )
    assert bad.status_code == 401

    # No token -> 403
    assert client.get(f"{API}/profile").status_code == 403


def test_weak_password_rejected(client):
    resp = client.post(f"{API}/register", json={"email": "weak@example.com", "password": "short"})
    assert resp.status_code == 422


def test_token_refresh(client):
    reg = client.post(
        f"{API}/register", json={"email": "refresh@example.com", "password": "password123"}
    )
    refresh_token = reg.json()["tokens"]["refresh_token"]

    refreshed = client.post(f"{API}/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]

    # An access token must not be accepted where a refresh token is expected.
    access = reg.json()["tokens"]["access_token"]
    assert client.post(f"{API}/refresh", json={"refresh_token": access}).status_code == 401
