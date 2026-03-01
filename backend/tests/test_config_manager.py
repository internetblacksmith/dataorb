"""Tests for ConfigManager — config backbone."""

import json
import os

import pytest


def test_missing_file_creates_defaults(tmp_config, config_manager):
    """When no config file exists, ConfigManager creates it with all default sections."""
    assert os.path.exists(tmp_config)
    config = config_manager.get_config()
    for section in ("posthog", "display", "network", "advanced", "ota", "custom_themes"):
        assert section in config, f"Missing default section: {section}"


def test_deep_merge_preserves_existing_values(config_manager):
    """Deep merge keeps user-set nested values when defaults are merged in."""
    config_manager.update_config({"posthog": {"api_key": "my-key"}})

    # Reload config (simulating restart)
    reloaded = config_manager.load_config()

    assert reloaded["posthog"]["api_key"] == "my-key"
    # Default host should still be present
    assert reloaded["posthog"]["host"] == "https://app.posthog.com"


def test_deep_merge_adds_new_default_keys(config_manager, tmp_config):
    """If a new default key is added, it appears after reload."""
    # Write a config that's missing the 'ota' section
    with open(tmp_config, "w") as f:
        json.dump({"posthog": {"api_key": "keep-me"}}, f)

    reloaded = config_manager.load_config()
    assert reloaded["posthog"]["api_key"] == "keep-me"
    assert "ota" in reloaded  # new default key added


def test_write_failure_returns_false(config_manager, monkeypatch):
    """save_config returns False on PermissionError."""
    monkeypatch.setattr(
        "builtins.open",
        lambda *a, **kw: (_ for _ in ()).throw(PermissionError("read-only")),
    )
    assert config_manager.save_config() is False


def test_get_config_returns_deep_copy(config_manager):
    """get_config returns a copy — mutating it doesn't affect internal state."""
    config = config_manager.get_config()
    config["posthog"]["api_key"] = "MUTATED"

    fresh = config_manager.get_config()
    assert fresh["posthog"]["api_key"] != "MUTATED"


def test_hash_changes_on_update(config_manager):
    """Config hash changes when config is updated."""
    hash_before = config_manager.get_config_hash()
    config_manager.update_config({"posthog": {"api_key": "new-key"}})
    hash_after = config_manager.get_config_hash()
    assert hash_before != hash_after


def test_hash_is_deterministic(config_manager):
    """Same config produces the same hash."""
    h1 = config_manager.get_config_hash()
    h2 = config_manager.get_config_hash()
    assert h1 == h2


def test_custom_theme_crud(config_manager):
    """Add, read, and delete a custom theme through ConfigManager."""
    theme_data = {"name": "Neon", "colors": {"background": "#000"}}
    assert config_manager.add_custom_theme("neon", theme_data) is True

    themes = config_manager.get_custom_themes()
    assert "neon" in themes
    assert themes["neon"]["name"] == "Neon"

    assert config_manager.delete_custom_theme("neon") is True
    assert "neon" not in config_manager.get_custom_themes()
