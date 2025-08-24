import json
import os
import logging
import hashlib
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self, config_file: str = "device_config.json"):
        self.config_file = config_file
        self.default_config = {
            "posthog": {
                "api_key": "",
                "project_id": "",
                "host": "https://app.posthog.com",
            },
            "display": {
                "refresh_interval": 60,
                "theme": "dark",
                "brightness": 100,
                "rotation": 0,
                "screensaver_timeout": 0,
                "metrics": {
                    "classic": {
                        "top": {"type": "events_24h", "label": "Events", "enabled": True},
                        "left": {"type": "unique_users_24h", "label": "Users", "enabled": True},
                        "right": {"type": "page_views_24h", "label": "Views", "enabled": True},
                    },
                    "modern": {
                        "top": {"type": "events_24h", "label": "Events", "enabled": True},
                        "left": {"type": "unique_users_24h", "label": "Users", "enabled": True},
                        "right": {"type": "page_views_24h", "label": "Views", "enabled": True},
                        "mini1": {"type": "sessions_24h", "label": "Sessions", "enabled": True},
                        "mini2": {
                            "type": "avg_events_per_user",
                            "label": "Avg/User",
                            "enabled": True,
                        },
                        "mini3": {"type": "events_1h", "label": "Events/h", "enabled": True},
                    },
                    "analytics": {
                        "top": {"type": "events_24h", "label": "Events", "enabled": True},
                        "left": {"type": "unique_users_24h", "label": "Users", "enabled": True},
                        "right": {"type": "page_views_24h", "label": "Views", "enabled": True},
                        "bottom": {"type": "sessions_24h", "label": "Sessions", "enabled": True},
                    },
                    "executive": {
                        "north": {"type": "events_24h", "label": "Events", "enabled": True},
                        "east": {"type": "page_views_24h", "label": "Views", "enabled": True},
                        "south": {"type": "unique_users_24h", "label": "Users", "enabled": True},
                        "west": {"type": "sessions_24h", "label": "Sessions", "enabled": True},
                    },
                },
            },
            "network": {
                "wifi_ssid": "",
                "wifi_password": "",
                "static_ip": "",
                "use_dhcp": True,
            },
            "advanced": {
                "debug_mode": False,
                "log_level": "INFO",
                "enable_telemetry": False,
            },
            "ota": {
                "enabled": True,
                "branch": "main",
                "check_on_boot": True,
                "auto_pull": False,
                "last_update": None,
                "last_check": None,
                "update_schedule": "0 3 * * *",  # Default: 3 AM daily
                "backup_before_update": True,
                "max_backups": 5,
            },
            "custom_themes": {},  # Store custom themes here
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create with defaults"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_configs(self.default_config, loaded_config)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return self.default_config.copy()
        else:
            # Create new config file with defaults
            self.save_config(self.default_config)
            return self.default_config.copy()

    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Save configuration to file"""
        try:
            config_to_save = config if config is not None else self.config
            with open(self.config_file, "w") as f:
                json.dump(config_to_save, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            # Merge updates with current config
            self.config = self._merge_configs(self.config, updates)
            return self.save_config()
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return False

    def get_posthog_config(self) -> Dict[str, str]:
        """Get PostHog configuration"""
        return self.config.get("posthog", {})

    def get_display_config(self) -> Dict[str, Any]:
        """Get display configuration"""
        return self.config.get("display", {})

    def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration"""
        return self.config.get("network", {})

    def get_config_hash(self) -> str:
        """Calculate hash of current configuration for change detection"""
        # Create a stable string representation of config
        # Sort keys to ensure consistent hashing
        config_str = json.dumps(self.config, sort_keys=True)
        # Return first 8 characters of SHA256 hash for brevity
        return hashlib.sha256(config_str.encode()).hexdigest()[:8]

    def get_ota_config(self) -> Dict[str, Any]:
        """Get OTA configuration"""
        return self.config.get("ota", {})

    def update_ota_config(self, updates: Dict[str, Any]) -> bool:
        """Update OTA configuration"""
        try:
            if "ota" not in self.config:
                self.config["ota"] = {}
            self.config["ota"].update(updates)
            return self.save_config()
        except Exception as e:
            logger.error(f"Error updating OTA config: {e}")
            return False

    def get_custom_themes(self) -> Dict[str, Any]:
        """Get custom themes"""
        return self.config.get("custom_themes", {})

    def add_custom_theme(self, theme_id: str, theme_data: Dict[str, Any]) -> bool:
        """Add or update a custom theme"""
        try:
            if "custom_themes" not in self.config:
                self.config["custom_themes"] = {}

            # Optional: Validate SVG logo if provided
            if "logo" in theme_data and theme_data["logo"]:
                if not isinstance(theme_data["logo"], str):
                    logger.error("Theme logo must be a string (SVG content)")
                    return False

            self.config["custom_themes"][theme_id] = theme_data
            return self.save_config()
        except Exception as e:
            logger.error(f"Error adding custom theme: {e}")
            return False

    def delete_custom_theme(self, theme_id: str) -> bool:
        """Delete a custom theme"""
        try:
            if "custom_themes" in self.config and theme_id in self.config["custom_themes"]:
                del self.config["custom_themes"][theme_id]
                return self.save_config()
            return False
        except Exception as e:
            logger.error(f"Error deleting custom theme: {e}")
            return False
