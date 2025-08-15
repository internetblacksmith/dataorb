import json
import os
from datetime import datetime
from typing import Dict, Any


class ConfigManager:
    def __init__(self, config_file: str = "device_config.json"):
        self.config_file = config_file
        self.default_config = {
            "device": {
                "name": "Pi Analytics Dashboard",
                "location": "Office",
                "timezone": "UTC",
                "last_configured": None,
            },
            "posthog": {
                "api_key": "",
                "project_id": "",
                "host": "https://app.posthog.com",
            },
            "display": {
                "refresh_interval": 30,
                "theme": "dark",
                "brightness": 100,
                "rotation": 0,
                "screensaver_timeout": 0,
                "metrics": {
                    "top": {"type": "events_24h", "label": "Events", "enabled": True},
                    "left": {
                        "type": "unique_users_24h",
                        "label": "Users",
                        "enabled": True,
                    },
                    "right": {
                        "type": "page_views_24h",
                        "label": "Views",
                        "enabled": True,
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
                print(f"Error loading config: {e}")
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
            print(f"Error saving config: {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            # Update timestamp
            if "device" not in updates:
                updates["device"] = {}
            updates["device"]["last_configured"] = datetime.now().isoformat()

            # Merge updates with current config
            self.config = self._merge_configs(self.config, updates)
            return self.save_config()
        except Exception as e:
            print(f"Error updating config: {e}")
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
            print(f"Error updating OTA config: {e}")
            return False