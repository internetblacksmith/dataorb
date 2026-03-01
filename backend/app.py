import logging
import os
import secrets
import socket
import subprocess
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, send_from_directory, request, render_template
from flask_cors import CORS
from functools import wraps

from config_manager import ConfigManager
from ota_manager import OTAManager
from themes import ThemeManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    static_folder="../frontend/build",
    static_url_path="/static-files",
    template_folder="templates",
)

CORS(app, resources={r"/api/*": {"origins": "self"}})

config_manager = ConfigManager()
ota_manager = OTAManager(config_manager)
theme_manager = ThemeManager(config_manager)


def _get_or_create_admin_token() -> str:
    """Get existing admin token or generate one on first boot"""
    config = config_manager.get_config()
    token = config.get("advanced", {}).get("admin_token")
    if not token:
        token = secrets.token_urlsafe(32)
        config_manager.update_config({"advanced": {"admin_token": token}})
        logger.info("Generated new admin token")
    return token


def require_admin(f):
    """Decorator requiring a valid admin token for protected endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Authorization required"}), 401
        token = auth[7:]
        if not secrets.compare_digest(token, _get_or_create_admin_token()):
            return jsonify({"error": "Invalid token"}), 403
        return f(*args, **kwargs)
    return decorated


@app.route("/api/auth/token")
def get_admin_token():
    """Return admin token — only accessible from the device itself"""
    if request.remote_addr not in ("127.0.0.1", "::1"):
        return jsonify({"error": "Only accessible from localhost"}), 403
    return jsonify({"token": _get_or_create_admin_token()})


# Load PostHog configuration from config file or environment
def get_posthog_config():
    """Get PostHog configuration from config file or environment variables"""
    config = config_manager.get_config()

    # Get from saved config
    api_key = config.get("posthog", {}).get("api_key")
    project_id = config.get("posthog", {}).get("project_id")
    host = config.get("posthog", {}).get("host", "https://app.posthog.com")

    return api_key, project_id, host


def get_default_metric_label(metric_type):
    """Get default label for a metric type"""
    labels = {
        "events_24h": "Events (24h)",
        "unique_users_24h": "Users (24h)",
        "page_views_24h": "Page Views (24h)",
        "custom_events_24h": "Custom Events (24h)",
        "sessions_24h": "Sessions (24h)",
        "events_1h": "Events (1h)",
        "avg_events_per_user": "Avg/User",
    }
    return labels.get(metric_type, metric_type.replace("_", " ").title())


DEMO_METRICS = {
    "events_24h": 142,
    "unique_users_24h": 37,
    "page_views_24h": 89,
    "custom_events_24h": 53,
    "sessions_24h": 24,
    "events_1h": 8,
    "avg_events_per_user": 3.8,
    "demo_mode": True,
}

LAYOUT_POSITION_MAPS = {
    "classic": {
        "positions": {"top": "top", "left": "left", "right": "right"},
        "extras": {},
    },
    "modern": {
        "positions": {
            "top": "primary",
            "left": "secondaryLeft",
            "right": "secondaryRight",
            "mini1": "miniStat1",
            "mini2": "miniStat2",
            "mini3": "miniStat3",
        },
        "extras": {"lastUpdated": True},
    },
    "analytics": {
        "positions": {
            "center": "center",
            "top": "top",
            "left": "left",
            "right": "right",
            "bottom": "bottom",
            "stat1": "stat1",
            "stat2": "stat2",
            "stat3": "stat3",
        },
        "extras": {"lastUpdated": True},
    },
    "executive": {
        "positions": {
            "north": "north",
            "east": "east",
            "south": "south",
            "west": "west",
            "northeast": "northEast",
            "southeast": "southEast",
            "southwest": "southWest",
            "northwest": "northWest",
        },
        "extras": {"lastUpdated": True, "recent_events": True},
    },
}


@app.route("/api/metrics/available")
def get_available_metrics():
    """Get list of available metrics for configuration"""
    return jsonify(
        {
            "events_24h": {
                "label": "Events (24h)",
                "description": "Total events in the last 24 hours",
            },
            "unique_users_24h": {
                "label": "Users (24h)",
                "description": "Unique users in the last 24 hours",
            },
            "page_views_24h": {
                "label": "Page Views (24h)",
                "description": "Page view events in the last 24 hours",
            },
            "custom_events_24h": {
                "label": "Custom Events (24h)",
                "description": "Non-pageview events in the last 24 hours",
            },
            "sessions_24h": {
                "label": "Sessions (24h)",
                "description": "Unique sessions in the last 24 hours",
            },
            "events_1h": {"label": "Events (1h)", "description": "Events in the last hour"},
            "avg_events_per_user": {
                "label": "Avg Events/User",
                "description": "Average events per user in the last 24 hours",
            },
        }
    )


def check_and_start_wap_if_needed():
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", "8.8.8.8"], 
            capture_output=True, 
            timeout=3
        )
        has_network = result.returncode == 0
        
        if not has_network:
            # Check if WAP is already running
            if not os.path.exists("/tmp/wifi_ap_mode"):
                # Start WAP immediately
                app_dir = os.path.dirname(os.path.abspath(__file__))
                script_path = os.path.join(app_dir, "..", "scripts", "wifi-ap-manager.sh")
                subprocess.run(
                    ["sudo", script_path, "start"],
                    timeout=30
                )
                return True  # WAP started
        return False  # No WAP needed
    except Exception:
        return False


def fetch_posthog_metrics():
    """Fetch metrics from PostHog API"""
    api_key, project_id, host = get_posthog_config()
    if not api_key or not project_id:
        return None, "PostHog credentials not configured"

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        events_url = f"{host}/api/projects/{project_id}/events"
        params = {
            "after": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "limit": "100",
        }

        response = requests.get(events_url, headers=headers, params=params, timeout=5)

        if response.status_code == 401:
            return None, "PostHog API error: 401 - Invalid API key"
        elif response.status_code == 403:
            return None, "PostHog API error: 403 - Missing permissions or wrong project"
        elif response.status_code != 200:
            return dict(DEMO_METRICS), None

        data = response.json()
        events = data.get("results", [])

        # If no events in last 24 hours, try last 7 days
        if not events:
            params["after"] = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            response = requests.get(events_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                events = data.get("results", [])

        # Calculate statistics
        events_24h = len(events)
        unique_users = len(set(e.get("distinct_id", "") for e in events))
        page_views = len([e for e in events if e.get("event") == "$pageview"])
        custom_events = len(
            [e for e in events if e.get("event") not in ["$pageview", "$pageleave"]]
        )
        sessions = len(
            set(
                e.get("properties", {}).get("$session_id", "")
                for e in events
                if e.get("properties", {}).get("$session_id")
            )
        )

        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        events_1h = len(
            [
                e
                for e in events
                if datetime.fromisoformat(e.get("timestamp", "").replace("Z", "+00:00"))
                > one_hour_ago
            ]
        )

        avg_events_per_user = round(events_24h / unique_users, 1) if unique_users > 0 else 0

        # Get recent events for activity feed
        recent_events = []
        for event in events[:10]:  # Last 10 events
            recent_events.append(
                {
                    "event": event.get("event", "Unknown"),
                    "user": event.get("distinct_id", "Anonymous")[:8],
                    "timestamp": event.get("timestamp", ""),
                    "properties": event.get("properties", {}),
                }
            )

        return {
            "events_24h": events_24h,
            "unique_users_24h": unique_users,
            "page_views_24h": page_views,
            "custom_events_24h": custom_events,
            "sessions_24h": sessions,
            "events_1h": events_1h,
            "avg_events_per_user": avg_events_per_user,
            "recent_events": recent_events,
            "demo_mode": False,
        }, None

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        # Network error - check if we need to start WAP
        check_and_start_wap_if_needed()
        return None, "NETWORK_ERROR"
    except Exception as e:
        logger.error("PostHog metrics fetch error: %s", e)
        return None, "FETCH_ERROR"


def fetch_dashboard_stats(layout_name):
    """Fetch and format stats for any dashboard layout."""
    layout_info = LAYOUT_POSITION_MAPS[layout_name]
    metrics, error = fetch_posthog_metrics()

    if error:
        return None, error

    config = config_manager.get_config()
    layout_config = config.get("display", {}).get("metrics", {}).get(layout_name, {})

    response = {"demo_mode": metrics.get("demo_mode", False)}

    if layout_info["extras"].get("lastUpdated"):
        response["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    if layout_info["extras"].get("recent_events"):
        response["recent_events"] = metrics.get("recent_events", [])

    for config_pos, response_key in layout_info["positions"].items():
        if config_pos in layout_config:
            metric_config = layout_config[config_pos]
            if metric_config.get("enabled"):
                metric_type = metric_config.get("type")
                label = metric_config.get("label") or get_default_metric_label(metric_type)
                response[response_key] = {
                    "label": label,
                    "value": metrics.get(metric_type, 0),
                }

    return response, None


@app.route("/api/stats/<layout>")
def get_layout_stats(layout):
    """Get stats for a specific dashboard layout."""
    if layout not in LAYOUT_POSITION_MAPS:
        return jsonify({"error": f"Unknown layout: {layout}"}), 404

    stats, error = fetch_dashboard_stats(layout)

    if error:
        if error == "NETWORK_ERROR":
            return jsonify({"error": "network_lost", "redirect": "/setup"}), 503
        return jsonify({"error": error}), 500

    return jsonify(stats)


@app.route("/api/stats")
def get_stats():
    """Get all PostHog metrics (layout-agnostic)."""
    metrics, error = fetch_posthog_metrics()

    if error:
        if error == "NETWORK_ERROR":
            return jsonify({"error": "network_lost", "redirect": "/setup"}), 503
        return jsonify({"error": error}), 500

    metrics["last_updated"] = datetime.now(timezone.utc).isoformat()
    return jsonify(metrics)


@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    # Check if we're in AP mode - but only if no network connection exists
    ap_mode = False

    # Check for active network connection (ethernet or wifi)
    import subprocess

    try:
        # Check if we have any active network connection with internet access
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", "8.8.8.8"], capture_output=True, text=True, timeout=2
        )
        has_internet = result.returncode == 0

        # Only consider AP mode if no internet and the marker file exists
        if not has_internet and os.path.exists("/tmp/wifi_ap_mode"):
            ap_mode = True
    except Exception:
        # If we can't determine network status, check the marker file
        ap_mode = os.path.exists("/tmp/wifi_ap_mode")

    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ap_mode": ap_mode,
        }
    )


@app.route("/api/network/scan")
def scan_networks():
    """Scan for available WiFi networks"""
    import subprocess
    
    networks = []
    try:
        # Use iwlist to scan for networks (works better in AP mode)
        result = subprocess.run(
            ["sudo", "iwlist", "wlan0", "scan"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            current_network = {}
            for line in result.stdout.split("\n"):
                line = line.strip()
                if "Cell " in line:
                    # New network found, save previous if exists
                    if current_network:
                        networks.append(current_network)
                    current_network = {}
                elif "ESSID:" in line:
                    ssid = line.split('ESSID:"')[1].rstrip('"') if 'ESSID:"' in line else ""
                    if ssid:
                        current_network["ssid"] = ssid
                elif "Quality=" in line:
                    try:
                        quality = line.split("Quality=")[1].split()[0]
                        current_network["quality"] = quality
                    except:
                        current_network["quality"] = "Unknown"
                elif "Encryption key:" in line:
                    current_network["encryption"] = "on" if "on" in line else "off"
                    
            # Add last network
            if current_network and "ssid" in current_network:
                networks.append(current_network)
                
        # Deduplicate by SSID
        seen = set()
        unique_networks = []
        for network in networks:
            if network.get("ssid") and network["ssid"] not in seen:
                seen.add(network["ssid"])
                unique_networks.append(network)
                
        return jsonify(unique_networks)
    except Exception as e:
        logger.error("Network scan error: %s", e)
        return jsonify({"error": "Failed to scan networks"}), 500


@app.route("/api/network/connect", methods=["POST"])
@require_admin
def connect_network():
    """Connect to a WiFi network"""
    import subprocess
    import re

    data = request.get_json()
    ssid = data.get("ssid")
    password = data.get("password")

    if not ssid:
        return jsonify({"success": False, "error": "SSID is required"}), 400

    # Validate SSID: 1-32 chars, printable ASCII, no quotes or backslashes
    if not re.match(r'^[a-zA-Z0-9 _\-\.]{1,32}$', ssid):
        return jsonify({"success": False, "error": "Invalid SSID format"}), 400

    # Validate password: 8-63 chars for WPA, printable ASCII only
    if password and (len(password) < 8 or len(password) > 63):
        return jsonify({"success": False, "error": "Password must be 8-63 characters"}), 400
    if password and not re.match(r'^[\x20-\x7E]+$', password):
        return jsonify({"success": False, "error": "Password contains invalid characters"}), 400

    try:
        # Write directly via sudo tee — no shell interpolation
        wpa_entry = f'\nnetwork={{\n    ssid="{ssid}"\n    psk="{password}"\n}}\n'
        subprocess.run(
            ["sudo", "tee", "-a", "/etc/wpa_supplicant/wpa_supplicant.conf"],
            input=wpa_entry, text=True, check=True, timeout=5,
            stdout=subprocess.DEVNULL
        )
        
        # Restart networking to apply changes
        subprocess.run(
            ["sudo", "systemctl", "restart", "wpa_supplicant"],
            check=True,
            timeout=10
        )
        
        # Stop AP mode if active
        if os.path.exists("/tmp/wifi_ap_mode"):
            subprocess.run(
                ["sudo", f"{os.path.dirname(os.path.abspath(__file__))}/../scripts/wifi-ap-manager.sh", "stop"],
                timeout=10
            )
            
        return jsonify({"success": True, "message": "Connecting to network..."})
        
    except Exception as e:
        logger.error("WiFi connect error: %s", e)
        return jsonify({"success": False, "error": "Failed to connect to network"}), 500


@app.route("/api/network/status")
def network_status():
    """Check network and AP mode status"""
    import subprocess

    # Check network connectivity first
    has_network = False
    has_ethernet = False
    wifi_ssid = ""
    wifi_signal = "0%"
    
    try:
        # Check for internet connectivity
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", "8.8.8.8"], capture_output=True, timeout=3
        )
        has_network = result.returncode == 0

        # Check if ethernet is connected
        eth_result = subprocess.run(
            ["ip", "link", "show", "eth0"], capture_output=True, text=True, timeout=2
        )
        if eth_result.returncode == 0 and "state UP" in eth_result.stdout:
            has_ethernet = True
            
        # Get WiFi status
        wifi_result = subprocess.run(
            ["iwconfig", "wlan0"], capture_output=True, text=True, timeout=2
        )
        if wifi_result.returncode == 0:
            for line in wifi_result.stdout.split("\n"):
                if "ESSID:" in line:
                    wifi_ssid = line.split('ESSID:"')[1].split('"')[0] if 'ESSID:"' in line else ""
                if "Link Quality" in line:
                    # Extract signal quality percentage
                    try:
                        quality = line.split("Link Quality=")[1].split()[0]
                        wifi_signal = quality
                    except:
                        wifi_signal = "0%"
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    # Check AP mode
    ap_mode = os.path.exists("/tmp/wifi_ap_mode")

    # Get current IP addresses
    ips = []
    connection_type = "none"
    try:
        result = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "inet " in line and "127.0.0.1" not in line:
                    ip = line.strip().split()[1].split("/")[0]
                    ips.append(ip)
                    # Determine connection type
                    if "eth0" in line:
                        connection_type = "ethernet"
                    elif "wlan0" in line or "wlan1" in line:
                        if not ap_mode:
                            connection_type = "wifi"

    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    # Format response to match frontend expectations
    return jsonify(
        {
            # Legacy fields for compatibility
            "ap_mode": ap_mode,
            "has_network": has_network,
            "connected": has_network,
            "connection_type": connection_type,
            "ip_addresses": ips,
            "ap_ssid": "DataOrb-Setup" if ap_mode else None,
            
            # New fields expected by SetupPage
            "network_connected": has_network,
            "ap_active": ap_mode,
            "wifi_status": {
                "status": "connected" if wifi_ssid and has_network else "disconnected",
                "ssid": wifi_ssid or (connection_type if connection_type == "ethernet" else "Not connected"),
                "signal": wifi_signal
            }
        }
    )


# OTA Update endpoints
@app.route("/api/admin/ota/status")
@require_admin
def get_ota_status():
    return jsonify(ota_manager.get_status())


@app.route("/api/admin/ota/check")
@require_admin
def check_for_updates():
    return jsonify(ota_manager.check_for_updates())


@app.route("/api/admin/ota/update", methods=["POST"])
@require_admin
def apply_update():
    """Apply OTA update"""
    result = ota_manager.perform_update()
    return jsonify(result)


@app.route("/api/admin/ota/config", methods=["GET", "POST"])
@require_admin
def ota_config():
    """Get or update OTA configuration"""
    if request.method == "GET":
        return jsonify(ota_manager.get_config())
    else:
        data = request.get_json()
        if ota_manager.update_config(data):
            return jsonify({"success": True})
        else:
            return (
                jsonify({"success": False, "error": "Failed to update OTA config"}),
                500,
            )


@app.route("/api/admin/ota/switch-branch", methods=["POST"])
@require_admin
def switch_branch():
    """Switch Git branch for OTA updates"""
    data = request.get_json()
    branch = data.get("branch")
    if not branch:
        return jsonify({"success": False, "error": "Branch name required"}), 400

    result = ota_manager.switch_branch(branch)
    return jsonify(result)


@app.route("/api/admin/ota/branches")
@require_admin
def get_branches():
    return jsonify(ota_manager.get_available_branches())


@app.route("/api/admin/ota/backups")
@require_admin
def get_backups():
    return jsonify(ota_manager.list_backups())


@app.route("/api/admin/ota/rollback", methods=["POST"])
@require_admin
def rollback():
    """Rollback to a specific backup"""
    data = request.get_json()
    backup_name = data.get("backup_name")
    if not backup_name:
        return jsonify({"success": False, "error": "Backup name required"}), 400

    result = ota_manager.rollback(backup_name)
    return jsonify(result)


@app.route("/api/admin/ota/update-cron", methods=["POST"])
@require_admin
def update_cron():
    """Update cron schedule for automatic updates"""
    data = request.get_json()
    schedule = data.get("schedule")
    if not schedule:
        return jsonify({"success": False, "error": "Schedule required"}), 400

    result = ota_manager.update_cron_schedule(schedule)
    return jsonify(result)


@app.route("/api/admin/ota/test-connection")
@require_admin
def test_git_connection():
    return jsonify(ota_manager.test_git_connection())


@app.route("/api/admin/ota/history")
@require_admin
def get_update_history():
    return jsonify(ota_manager.get_logs())


@app.route("/api/admin/ota/clean-cache", methods=["POST"])
@require_admin
def clean_cache():
    """Clean OTA cache and temporary files"""
    return jsonify(ota_manager.clean_cache())


# Theme management endpoints
@app.route("/api/themes")
def get_themes():
    """Get list of all available themes"""
    return jsonify(theme_manager.get_theme_list())


@app.route("/api/themes/<theme_id>")
def get_theme(theme_id):
    """Get a specific theme by ID"""
    theme = theme_manager.get_theme(theme_id)
    if theme:
        return jsonify(theme)
    return jsonify({"error": "Theme not found"}), 404


@app.route("/api/themes/<theme_id>/export")
def export_theme(theme_id):
    """Export a theme as downloadable JSON"""
    theme_data = theme_manager.export_theme(theme_id)
    if theme_data:
        return jsonify(theme_data)
    return jsonify({"error": "Theme not found"}), 404


@app.route("/api/themes/import", methods=["POST"])
@require_admin
def import_theme():
    """Import a theme from uploaded JSON"""
    try:
        theme_data = request.get_json()
        if theme_manager.import_theme(theme_data):
            return jsonify({"success": True, "message": "Theme imported successfully"})
        return jsonify({"success": False, "error": "Invalid theme format"}), 400
    except Exception as e:
        logger.error("Theme import error: %s", e)
        return jsonify({"success": False, "error": "Failed to import theme"}), 500


@app.route("/api/themes/custom", methods=["POST"])
@require_admin
def add_custom_theme():
    """Add or update a custom theme"""
    try:
        data = request.get_json()
        theme_id = data.get("id")
        theme_data = data.get("theme")

        if not theme_id or not theme_data:
            return jsonify({"success": False, "error": "Missing theme ID or data"}), 400

        if theme_manager.add_custom_theme(theme_id, theme_data):
            return jsonify({"success": True, "message": "Theme saved successfully"})
        return jsonify({"success": False, "error": "Invalid theme data"}), 400
    except Exception as e:
        logger.error("Custom theme save error: %s", e)
        return jsonify({"success": False, "error": "Failed to save theme"}), 500


@app.route("/api/themes/custom/<theme_id>", methods=["DELETE"])
@require_admin
def delete_custom_theme(theme_id):
    """Delete a custom theme"""
    if theme_manager.delete_custom_theme(theme_id):
        return jsonify({"success": True, "message": "Theme deleted successfully"})
    return jsonify({"success": False, "error": "Theme not found or is built-in"}), 404


# Configuration endpoints
@app.route("/api/admin/config")
@require_admin
def get_config():
    config = config_manager.get_config()

    # Add actual device IP address
    try:
        # Get IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()

        # Add to network config
        if "network" not in config:
            config["network"] = {}
        config["network"]["ip_address"] = ip_address
    except (OSError, socket.error):
        config.setdefault("network", {})["ip_address"] = "localhost"

    return jsonify(config)


@app.route("/api/admin/config", methods=["POST"])
@require_admin
def update_config():
    data = request.get_json()

    allowed_keys = {"posthog", "display", "network", "advanced", "ota", "custom_themes"}
    rejected = set(data.keys()) - allowed_keys
    if rejected:
        return jsonify({"success": False, "error": f"Unknown config keys: {rejected}"}), 400

    if not config_manager.update_config(data):
        return jsonify({"success": False, "error": "Failed to update config"}), 500

    return jsonify({"success": True})


@app.route("/api/config/version")
def get_config_version():
    """Get config version hash for change detection"""
    return jsonify(
        {
            "version": config_manager.get_config_hash(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/api/admin/config/validate/posthog", methods=["POST"])
@require_admin
def validate_posthog_config():
    """Validate PostHog configuration"""
    data = request.get_json()

    # Check required fields
    if not data.get("api_key"):
        return jsonify({"valid": False, "error": "API key is required"}), 400

    if not data.get("project_id"):
        return jsonify({"valid": False, "error": "Project ID is required"}), 400

    # Test the configuration by making a request to PostHog
    api_key = data.get("api_key")
    project_id = data.get("project_id")
    host = data.get("host", "https://app.posthog.com")

    parsed = urlparse(host)
    if not parsed.hostname or not (parsed.hostname == "posthog.com" or parsed.hostname.endswith(".posthog.com")):
        return jsonify({"valid": False, "error": "Host must be a posthog.com domain"}), 400

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Try to fetch project info to validate credentials
        test_url = f"{host}/api/projects/{project_id}/"
        response = requests.get(test_url, headers=headers, timeout=10)

        if response.status_code == 200:
            return jsonify({"valid": True, "message": "PostHog connection successful"})
        elif response.status_code == 401:
            return jsonify({"valid": False, "error": "Invalid API key"}), 401
        elif response.status_code == 403:
            return (
                jsonify(
                    {"valid": False, "error": "API key doesn't have access to this project"}
                ),
                403,
            )
        elif response.status_code == 404:
            return (
                jsonify({"valid": False, "error": "Project not found. Check your Project ID"}),
                404,
            )
        else:
            return (
                jsonify({"valid": False, "error": f"PostHog API error: {response.status_code}"}),
                response.status_code,
            )

    except requests.exceptions.Timeout:
        return (
            jsonify(
                {"valid": False, "error": "Connection timeout. Check your network or host URL"}
            ),
            408,
        )
    except requests.exceptions.ConnectionError:
        return (
            jsonify(
                {"valid": False, "error": "Could not connect to PostHog. Check the host URL"}
            ),
            503,
        )
    except Exception as e:
        logger.error("PostHog connection test error: %s", e)
        return jsonify({"valid": False, "error": "Error testing connection"}), 500


@app.route("/api/admin/config", methods=["DELETE"])
@require_admin
def delete_config():
    """Clear PostHog credentials from the device config."""
    try:
        config_manager.update_config({"posthog": {"api_key": "", "project_id": "", "host": "https://app.posthog.com"}})
        return jsonify({"success": True, "message": "Configuration deleted successfully"})
    except Exception as e:
        logger.error("Config deletion error: %s", e)
        return jsonify({"success": False, "error": "Failed to delete configuration"}), 500


# Serve static files (JS, CSS, images)
@app.route("/static/<path:path>")
def serve_static(path):
    """Serve static files from React build"""
    return send_from_directory(os.path.join(app.static_folder, "static"), path)


@app.route("/manifest.json")
def serve_manifest():
    """Serve manifest.json"""
    return send_from_directory(app.static_folder, "manifest.json")


@app.route("/favicon.ico")
def serve_favicon():
    """Serve favicon.ico"""
    return send_from_directory(app.static_folder, "favicon.ico")


@app.route("/robots.txt")
def serve_robots():
    """Serve robots.txt"""
    return send_from_directory(app.static_folder, "robots.txt")


# Serve layout preview images
@app.route("/layout-previews/<path:filename>")
def serve_layout_preview(filename):
    """Serve layout preview images"""
    preview_dir = os.path.join(app.static_folder, "layout-previews")
    if os.path.exists(os.path.join(preview_dir, filename)):
        return send_from_directory(preview_dir, filename)
    else:
        return "Image not found", 404


# Serve React App for all other routes - This MUST be after all API and static routes
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path):
    """Serve the React application for all non-API routes with embedded theme data"""
    # Don't serve API routes
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404

    # Get current display config and theme
    config = config_manager.get_config()
    display_config = config.get("display", {})
    theme_id = display_config.get("theme", "dark")

    # Get theme data
    theme_data = None
    if theme_id and theme_id not in ["dark", "light"]:
        theme_data = theme_manager.get_theme(theme_id)

    # Find the actual build files (they have hashes in the names)
    js_files = []
    css_files = []

    static_js_path = os.path.join(app.static_folder, "static", "js")
    static_css_path = os.path.join(app.static_folder, "static", "css")

    if os.path.exists(static_js_path):
        for file in os.listdir(static_js_path):
            if file.startswith("main.") and file.endswith(".js") and not file.endswith(".map"):
                js_files.append(file)

    if os.path.exists(static_css_path):
        for file in os.listdir(static_css_path):
            if file.startswith("main.") and file.endswith(".css") and not file.endswith(".map"):
                css_files.append(file)

    # For all routes (including /config, /setup), serve index.html with embedded data
    # This allows React Router to handle client-side routing
    return render_template(
        "index.html",
        theme_data=theme_data,
        display_config=display_config,
        js_files=js_files,
        css_files=css_files,
    )


if __name__ == "__main__":
    # Perform boot update check if enabled
    try:
        boot_result = ota_manager.perform_boot_update()
        if boot_result.get("error"):
            logger.warning("Boot update warning: %s", boot_result["error"])
        elif boot_result.get("success"):
            logger.info("Boot update completed successfully")
    except Exception as e:
        logger.error("Boot update check failed: %s", e)

    # Check if we're in debug mode
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"

    # In debug mode, use port 5000. In production, try port 80 first
    if debug_mode:
        port = 5000
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        # Run on port 80 for production IoT device (requires capability or root)
        # Falls back to port 5000 if port 80 is not available
        port = 80
        try:
            app.run(host="0.0.0.0", port=port, debug=False)
        except PermissionError:
            logger.warning("Cannot bind to port 80, falling back to port 5000")
            port = 5000
            app.run(host="0.0.0.0", port=port, debug=False)
