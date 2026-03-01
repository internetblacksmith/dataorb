"""Tests for ThemeManager."""

import pytest

from themes import ThemeManager


@pytest.fixture
def theme_mgr(config_manager):
    return ThemeManager(config_manager)


def test_theme_list_includes_built_ins(theme_mgr):
    """Theme list contains dark and light with isCustom: False."""
    themes = theme_mgr.get_theme_list()
    ids = {t["id"] for t in themes}
    assert "dark" in ids
    assert "light" in ids
    for t in themes:
        if t["id"] in ("dark", "light"):
            assert t["isCustom"] is False


def test_import_builtin_id_gets_suffixed(theme_mgr):
    """Importing a theme with id 'dark' saves it as 'dark_custom'."""
    theme_data = {
        "id": "dark",
        "name": "Custom Dark",
        "colors": {"background": "#111"},
    }
    assert theme_mgr.import_theme(theme_data) is True

    themes = theme_mgr.get_theme_list()
    ids = {t["id"] for t in themes}
    assert "dark_custom" in ids


def test_delete_builtin_returns_false(theme_mgr):
    """Built-in themes cannot be deleted."""
    assert theme_mgr.delete_custom_theme("dark") is False


def test_delete_custom_returns_true(theme_mgr):
    """Custom themes can be deleted."""
    theme_mgr.add_custom_theme("my-theme", {"name": "My Theme", "colors": {}})
    assert theme_mgr.delete_custom_theme("my-theme") is True

    themes = theme_mgr.get_theme_list()
    ids = {t["id"] for t in themes}
    assert "my-theme" not in ids


def test_custom_theme_has_is_custom_true(theme_mgr):
    """Custom themes are returned with isCustom: True."""
    theme_mgr.add_custom_theme("ocean", {"name": "Ocean", "colors": {}})
    themes = theme_mgr.get_theme_list()
    ocean = next(t for t in themes if t["id"] == "ocean")
    assert ocean["isCustom"] is True


def test_export_has_expected_shape(theme_mgr):
    """Exported theme has id, name, colors, logo keys."""
    exported = theme_mgr.export_theme("dark")
    assert exported is not None
    for key in ("id", "name", "colors", "logo"):
        assert key in exported
