"""Tests for authentication and authorization."""

from unittest.mock import patch

import pytest


def test_token_from_localhost_returns_200(app_client):
    """GET /api/auth/token from 127.0.0.1 returns a valid token."""
    response = app_client.get("/api/auth/token", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert response.status_code == 200
    data = response.get_json()
    assert "token" in data
    assert len(data["token"]) > 20  # secrets.token_urlsafe(32) is ~43 chars


def test_token_from_remote_ip_returns_403(app_client):
    """GET /api/auth/token from a remote IP is forbidden."""
    response = app_client.get("/api/auth/token", environ_base={"REMOTE_ADDR": "192.168.1.100"})
    assert response.status_code == 403


def test_admin_route_without_auth_returns_401(app_client):
    """Protected routes without Authorization header return 401."""
    response = app_client.get("/api/admin/config")
    assert response.status_code == 401


def test_admin_route_with_bad_token_returns_403(app_client):
    """Protected routes with an invalid token return 403."""
    response = app_client.get(
        "/api/admin/config",
        headers={"Authorization": "Bearer totally-wrong-token"},
    )
    assert response.status_code == 403


def test_admin_route_with_valid_token_returns_200(app_client, auth_headers):
    """Protected routes with a valid token succeed."""
    response = app_client.get("/api/admin/config", headers=auth_headers)
    assert response.status_code == 200


def test_token_is_stable_across_calls(app_client):
    """The admin token is generated once and persists across calls."""
    resp1 = app_client.get("/api/auth/token", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    resp2 = app_client.get("/api/auth/token", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert resp1.get_json()["token"] == resp2.get_json()["token"]


def test_timing_safe_comparison_used(app_client, monkeypatch):
    """Token comparison uses secrets.compare_digest (timing-safe)."""
    import secrets

    original = secrets.compare_digest
    calls = []

    def spy(a, b):
        calls.append((a, b))
        return original(a, b)

    monkeypatch.setattr("secrets.compare_digest", spy)

    # Get a valid token
    token_resp = app_client.get("/api/auth/token", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    token = token_resp.get_json()["token"]

    # Use it on a protected route
    app_client.get("/api/admin/config", headers={"Authorization": f"Bearer {token}"})

    assert len(calls) > 0, "secrets.compare_digest was never called"
