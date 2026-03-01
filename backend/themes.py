import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Built-in theme definitions with CSS variable mappings
BUILT_IN_THEMES = {
    "dark": {
        "id": "dark",
        "name": "Dark",
        "description": "Default dark theme",
        "colors": {
            "background": "linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%)",
            "containerBg": "radial-gradient(circle, #1a1a1a 0%, #0a0a0a 100%)",
            "textColor": "#ffffff",
            "textSecondary": "#888888",
            "accent": "#f97316",
            "accentSecondary": "#fb923c",
            "border": "rgba(249, 115, 22, 0.5)",
            "shadow": "rgba(249, 115, 22, 0.3)",
            "statBg": "linear-gradient(135deg, rgba(249, 115, 22, 0.2) 0%, rgba(251, 146, 60, 0.2) 100%)",
            "statBorder": "rgba(249, 115, 22, 0.4)",
            "statValue": "linear-gradient(135deg, #f97316 0%, #fb923c 100%)",
            "statLabel": "#888888",
            "glowPrimary": "rgba(249, 115, 22, 0.5)",
            "glowSecondary": "rgba(251, 146, 60, 0.1)",
            "statusDot": "#48bb78",
        },
        "custom": False,
    },
    "light": {
        "id": "light",
        "name": "Light",
        "description": "Clean light theme",
        "colors": {
            "background": "linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)",
            "containerBg": "radial-gradient(circle, #ffffff 0%, #f0f0f0 100%)",
            "textColor": "#1a1a1a",
            "textSecondary": "#666666",
            "accent": "#f97316",
            "accentSecondary": "#ea580c",
            "border": "rgba(0, 0, 0, 0.15)",
            "shadow": "rgba(0, 0, 0, 0.1)",
            "statBg": "linear-gradient(135deg, rgba(249, 115, 22, 0.1) 0%, rgba(234, 88, 12, 0.1) 100%)",
            "statBorder": "rgba(249, 115, 22, 0.3)",
            "statValue": "linear-gradient(135deg, #ea580c 0%, #f97316 100%)",
            "statLabel": "#666666",
            "glowPrimary": "rgba(249, 115, 22, 0.3)",
            "glowSecondary": "rgba(234, 88, 12, 0.05)",
            "statusDot": "#22c55e",
        },
        "custom": False,
    },
}


class ThemeManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager

    def get_theme_list(self) -> List[Dict[str, Any]]:
        """Get list of all available themes (built-in + custom)"""
        themes = []

        for theme in BUILT_IN_THEMES.values():
            themes.append({
                "id": theme["id"],
                "name": theme["name"],
                "description": theme.get("description", ""),
                "custom": False,
            })

        custom_themes = self.config_manager.get_custom_themes()
        for theme_id, theme_data in custom_themes.items():
            themes.append({
                "id": theme_id,
                "name": theme_data.get("name", theme_id),
                "description": theme_data.get("description", ""),
                "custom": True,
                "isCustom": True,
            })

        return themes

    def get_theme(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific theme by ID"""
        if theme_id in BUILT_IN_THEMES:
            return BUILT_IN_THEMES[theme_id]

        custom_themes = self.config_manager.get_custom_themes()
        if theme_id in custom_themes:
            theme = custom_themes[theme_id].copy()
            theme["id"] = theme_id
            theme["custom"] = True
            theme["isCustom"] = True
            return theme

        return None

    def export_theme(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """Export a theme as a portable dict"""
        theme = self.get_theme(theme_id)
        if not theme:
            return None

        return {
            "id": theme["id"],
            "name": theme.get("name", theme_id),
            "description": theme.get("description", ""),
            "colors": theme.get("colors", {}),
            "logo": theme.get("logo"),
        }

    def import_theme(self, theme_data: Dict[str, Any]) -> bool:
        """Import a theme from a dict"""
        if not theme_data or not isinstance(theme_data, dict):
            return False

        theme_id = theme_data.get("id")
        if not theme_id:
            return False

        # Don't overwrite built-in themes
        if theme_id in BUILT_IN_THEMES:
            theme_id = f"{theme_id}_custom"

        return self.config_manager.add_custom_theme(theme_id, {
            "name": theme_data.get("name", theme_id),
            "description": theme_data.get("description", ""),
            "colors": theme_data.get("colors", {}),
            "logo": theme_data.get("logo"),
        })

    def add_custom_theme(self, theme_id: str, theme_data: Dict[str, Any]) -> bool:
        """Add or update a custom theme"""
        return self.config_manager.add_custom_theme(theme_id, theme_data)

    def delete_custom_theme(self, theme_id: str) -> bool:
        """Delete a custom theme (built-in themes cannot be deleted)"""
        if theme_id in BUILT_IN_THEMES:
            return False
        return self.config_manager.delete_custom_theme(theme_id)
