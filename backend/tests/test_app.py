"""Route-level tests for non-PostHog endpoints."""

from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Health & Metrics
# ---------------------------------------------------------------------------


@patch("app.subprocess.run")
def test_health_returns_200_and_healthy(mock_subprocess, app_client):
    """GET /api/health returns status: healthy."""
    mock_subprocess.return_value = type("R", (), {"returncode": 0})()
    response = app_client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_available_metrics_returns_all_7(app_client):
    """GET /api/metrics/available includes all 7 metric types."""
    response = app_client.get("/api/metrics/available")
    assert response.status_code == 200
    data = response.get_json()
    expected = {
        "events_24h", "unique_users_24h", "page_views_24h",
        "custom_events_24h", "sessions_24h", "events_1h", "avg_events_per_user",
    }
    assert expected == set(data.keys())


# ---------------------------------------------------------------------------
# Config CRUD
# ---------------------------------------------------------------------------


def test_config_post_rejects_unknown_keys(app_client, auth_headers):
    """POST /api/admin/config rejects keys not in the allow-list."""
    response = app_client.post(
        "/api/admin/config",
        json={"hacker_key": "bad"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Unknown config keys" in response.get_json()["error"]


def test_config_post_accepts_valid_keys(app_client, auth_headers):
    """POST /api/admin/config accepts allowed keys."""
    response = app_client.post(
        "/api/admin/config",
        json={"display": {"theme": "light"}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_config_delete_clears_posthog_creds(app_client, auth_headers):
    """DELETE /api/admin/config clears PostHog credentials."""
    # First set some credentials
    app_client.post(
        "/api/admin/config",
        json={"posthog": {"api_key": "secret", "project_id": "123"}},
        headers=auth_headers,
    )

    response = app_client.delete("/api/admin/config", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    # Verify credentials are cleared
    config_resp = app_client.get("/api/admin/config", headers=auth_headers)
    config = config_resp.get_json()
    assert config["posthog"]["api_key"] == ""
    assert config["posthog"]["project_id"] == ""


# ---------------------------------------------------------------------------
# PostHog Validation
# ---------------------------------------------------------------------------


def test_posthog_validation_rejects_non_posthog_host(app_client, auth_headers):
    """SSRF guard: non-posthog.com hosts are rejected."""
    response = app_client.post(
        "/api/admin/config/validate/posthog",
        json={"api_key": "phx_test", "project_id": "1", "host": "https://evil.com"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "posthog.com" in data["error"]


def test_posthog_validation_rejects_missing_api_key(app_client, auth_headers):
    """Validation requires an API key."""
    response = app_client.post(
        "/api/admin/config/validate/posthog",
        json={"project_id": "1"},
        headers=auth_headers,
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Network Connect — input validation
# ---------------------------------------------------------------------------


def test_network_connect_rejects_shell_injection_ssid(app_client, auth_headers):
    """SSID with shell injection characters is rejected."""
    response = app_client.post(
        "/api/network/connect",
        json={"ssid": "evil; rm -rf /", "password": "safepassword123"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Invalid SSID" in response.get_json()["error"]


def test_network_connect_rejects_short_password(app_client, auth_headers):
    """WPA password under 8 characters is rejected."""
    response = app_client.post(
        "/api/network/connect",
        json={"ssid": "MyNetwork", "password": "short"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "8-63 characters" in response.get_json()["error"]


# ---------------------------------------------------------------------------
# Config Version
# ---------------------------------------------------------------------------


def test_config_version_returns_hash_and_timestamp(app_client):
    """GET /api/config/version returns a version hash and timestamp."""
    response = app_client.get("/api/config/version")
    assert response.status_code == 200
    data = response.get_json()
    assert "version" in data
    assert len(data["version"]) == 8  # first 8 chars of SHA256
    assert "timestamp" in data
