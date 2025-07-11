import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, config_file: str = "device_config.json"):
        self.config_file = config_file
        self.default_config = {
            "device": {
                "name": "PostHog Pi Dashboard",
                "location": "Office",
                "timezone": "UTC",
                "last_configured": None
            },
            "posthog": {
                "api_key": "",
                "project_id": "",
                "host": "https://app.posthog.com"
            },
            "display": {
                "refresh_interval": 30,
                "theme": "dark",
                "brightness": 100,
                "rotation": 0,
                "screensaver_timeout": 0,
                "metrics": {
                    "top": {"type": "events_24h", "label": "Events", "enabled": True},
                    "left": {"type": "unique_users_24h", "label": "Users", "enabled": True},
                    "right": {"type": "page_views_24h", "label": "Views", "enabled": True}
                }
            },
            "network": {
                "wifi_ssid": "",
                "wifi_password": "",
                "static_ip": "",
                "use_dhcp": True
            },
            "advanced": {
                "debug_mode": False,
                "log_level": "INFO",
                "auto_update": True,
                "backup_enabled": True
            },
            "ota": {
                "enabled": True,
                "branch": "main",
                "check_on_boot": True,
                "auto_pull": True,
                "last_update": None,
                "last_check": None
            }
        }
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self.config = self._merge_configs(self.default_config, loaded_config)
            else:
                self.config = self.default_config.copy()
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self.default_config.copy()
        
        return self.config
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            self.config["device"]["last_configured"] = datetime.now().isoformat()
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get specific configuration section"""
        return self.config.get(section, {})
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            self.config = self._merge_configs(self.config, updates)
            return self.save_config()
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
    
    def update_section(self, section: str, updates: Dict[str, Any]) -> bool:
        """Update specific configuration section"""
        try:
            if section in self.config:
                self.config[section].update(updates)
            else:
                self.config[section] = updates
            return self.save_config()
        except Exception as e:
            print(f"Error updating section {section}: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        self.config = self.default_config.copy()
        return self.save_config()
    
    def export_config(self) -> str:
        """Export configuration as JSON string"""
        return json.dumps(self.config, indent=2)
    
    def import_config(self, config_json: str) -> bool:
        """Import configuration from JSON string"""
        try:
            imported_config = json.loads(config_json)
            self.config = self._merge_configs(self.default_config, imported_config)
            return self.save_config()
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def validate_posthog_config(self) -> Dict[str, Any]:
        """Validate PostHog configuration"""
        posthog_config = self.get_section("posthog")
        errors = []
        
        if not posthog_config.get("api_key"):
            errors.append("API key is required")
        
        if not posthog_config.get("project_id"):
            errors.append("Project ID is required")
        
        if not posthog_config.get("host"):
            errors.append("Host URL is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def get_env_vars(self) -> Dict[str, str]:
        """Get environment variables for PostHog"""
        posthog_config = self.get_section("posthog")
        return {
            "POSTHOG_API_KEY": posthog_config.get("api_key", ""),
            "POSTHOG_PROJECT_ID": posthog_config.get("project_id", ""),
            "POSTHOG_HOST": posthog_config.get("host", "https://app.posthog.com")
        }
    
    def _merge_configs(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result