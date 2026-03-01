import json
import os
import secrets

import pytest


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config file with defaults."""
    config_file = tmp_path / "device_config.json"
    return str(config_file)


@pytest.fixture
def config_manager(tmp_config):
    """Isolated ConfigManager using a temp config file."""
    from config_manager import ConfigManager

    return ConfigManager(config_file=tmp_config)


@pytest.fixture
def app_client(tmp_config, monkeypatch):
    """Flask test client with isolated config, OTA, and theme managers."""
    import app as app_module
    from config_manager import ConfigManager
    from ota_manager import OTAManager
    from themes import ThemeManager

    cm = ConfigManager(config_file=tmp_config)
    om = OTAManager(cm)
    tm = ThemeManager(cm)

    monkeypatch.setattr(app_module, "config_manager", cm)
    monkeypatch.setattr(app_module, "ota_manager", om)
    monkeypatch.setattr(app_module, "theme_manager", tm)

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client


@pytest.fixture
def admin_token(app_client):
    """Get a valid admin token from the test app."""
    response = app_client.get("/api/auth/token", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    return response.get_json()["token"]


@pytest.fixture
def auth_headers(admin_token):
    """Authorization headers with a valid admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def configured_posthog(app_client, auth_headers):
    """Pre-seed config with test PostHog credentials."""
    app_client.post(
        "/api/admin/config",
        json={
            "posthog": {
                "api_key": "phx_test_key_abc123",
                "project_id": "12345",
                "host": "https://app.posthog.com",
            }
        },
        headers=auth_headers,
    )
