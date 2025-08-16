from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import requests
import os
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from config_manager import ConfigManager
from ota_manager import OTAManager
from themes import ThemeManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configure Flask to serve React build files
# Don't use static_url_path="" as it interferes with routing
app = Flask(__name__, static_folder="../frontend/build", static_url_path="/static-files")

CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize managers
config_manager = ConfigManager()
ota_manager = OTAManager(config_manager)
theme_manager = ThemeManager(config_manager)


# Load PostHog configuration from config file or environment
def get_posthog_config():
    """Get PostHog configuration from config file or environment variables"""
    config = config_manager.get_config()

    # Try to get from saved config first
    api_key = config.get("posthog", {}).get("api_key") or os.getenv("POSTHOG_API_KEY")
    project_id = config.get("posthog", {}).get("project_id") or os.getenv(
        "POSTHOG_PROJECT_ID"
    )
    host = config.get("posthog", {}).get("host") or os.getenv(
        "POSTHOG_HOST", "https://app.posthog.com"
    )

    return api_key, project_id, host


@app.route("/api/metrics/available")
def get_available_metrics():
    """Get list of available metrics for configuration"""
    return jsonify({
        "events_24h": {
            "label": "Events (24h)",
            "description": "Total events in the last 24 hours"
        },
        "unique_users_24h": {
            "label": "Users (24h)",
            "description": "Unique users in the last 24 hours"
        },
        "page_views_24h": {
            "label": "Page Views (24h)",
            "description": "Page view events in the last 24 hours"
        },
        "custom_events_24h": {
            "label": "Custom Events (24h)",
            "description": "Non-pageview events in the last 24 hours"
        },
        "sessions_24h": {
            "label": "Sessions (24h)",
            "description": "Unique sessions in the last 24 hours"
        },
        "events_1h": {
            "label": "Events (1h)",
            "description": "Events in the last hour"
        },
        "avg_events_per_user": {
            "label": "Avg Events/User",
            "description": "Average events per user in the last 24 hours"
        }
    })


@app.route("/api/stats")
def get_stats():
    """Get basic DataOrb statistics"""
    # Get current PostHog configuration
    POSTHOG_API_KEY, POSTHOG_PROJECT_ID, POSTHOG_HOST = get_posthog_config()

    if not POSTHOG_API_KEY or not POSTHOG_PROJECT_ID:
        return jsonify({"error": "PostHog credentials not configured"})

    try:
        headers = {
            "Authorization": f"Bearer {POSTHOG_API_KEY}",
            "Content-Type": "application/json",
        }

        # Get events for last 24 hours (or 7 days if no recent events)
        events_url = f"{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/events"
        
        # First try last 24 hours
        params = {
            "after": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "limit": "100",
        }

        response = requests.get(events_url, headers=headers, params=params)

        if response.status_code == 401:
            return jsonify({"error": "PostHog API error: 401 - Invalid API key"}), 401
        elif response.status_code == 403:
            return (
                jsonify(
                    {
                        "error": "PostHog API error: 403 - Missing permissions or wrong project"
                    }
                ),
                403,
            )
        elif response.status_code != 200:
            return (
                jsonify({"error": f"PostHog API error: {response.status_code}"}),
                response.status_code,
            )

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

        # Get sessions count (unique session IDs)
        sessions = len(
            set(
                e.get("properties", {}).get("$session_id", "")
                for e in events
                if e.get("properties", {}).get("$session_id")
            )
        )

        # Get events from last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        events_1h = len(
            [
                e
                for e in events
                if datetime.fromisoformat(e.get("timestamp", "").replace("Z", "+00:00"))
                > one_hour_ago
            ]
        )

        # Calculate average events per user
        avg_events_per_user = (
            round(events_24h / unique_users, 1) if unique_users > 0 else 0
        )

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

        return jsonify(
            {
                "events_24h": events_24h,
                "unique_users_24h": unique_users,
                "page_views_24h": page_views,
                "custom_events_24h": custom_events,
                "sessions_24h": sessions,
                "events_1h": events_1h,
                "avg_events_per_user": avg_events_per_user,
                "recent_events": recent_events,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    # Check if we're in AP mode
    ap_mode = os.path.exists("/tmp/wifi_ap_mode")

    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ap_mode": ap_mode,
        }
    )


@app.route("/api/network/status")
def network_status():
    """Check network and AP mode status"""
    import subprocess

    # Check if AP mode marker exists
    ap_mode = os.path.exists("/tmp/wifi_ap_mode")

    # Check network connectivity
    has_network = False
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", "8.8.8.8"], capture_output=True, timeout=3
        )
        has_network = result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    # Get current IP addresses
    ips = []
    try:
        result = subprocess.run(
            ["ip", "addr", "show"], capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "inet " in line and "127.0.0.1" not in line:
                    ip = line.strip().split()[1].split("/")[0]
                    ips.append(ip)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    return jsonify(
        {
            "ap_mode": ap_mode,
            "has_network": has_network,
            "ip_addresses": ips,
            "ap_ssid": "DataOrb-Setup" if ap_mode else None,
            "ap_password": "dataorb123" if ap_mode else None,
        }
    )


# OTA Update endpoints
@app.route("/api/admin/ota/status")
def get_ota_status():
    """Get OTA update status"""
    return jsonify(ota_manager.get_status())


@app.route("/api/admin/ota/check")
def check_for_updates():
    """Check for available OTA updates"""
    return jsonify(ota_manager.check_for_updates())


@app.route("/api/admin/ota/update", methods=["POST"])
def apply_update():
    """Apply OTA update"""
    result = ota_manager.apply_update()
    return jsonify(result)


@app.route("/api/admin/ota/config", methods=["GET", "POST"])
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
def switch_branch():
    """Switch Git branch for OTA updates"""
    data = request.get_json()
    branch = data.get("branch")
    if not branch:
        return jsonify({"success": False, "error": "Branch name required"}), 400

    result = ota_manager.switch_branch(branch)
    return jsonify(result)


@app.route("/api/admin/ota/branches")
def get_branches():
    """Get available Git branches"""
    return jsonify(ota_manager.get_available_branches())


@app.route("/api/admin/ota/backups")
def get_backups():
    """Get list of available backups"""
    return jsonify(ota_manager.get_backups())


@app.route("/api/admin/ota/rollback", methods=["POST"])
def rollback():
    """Rollback to a specific backup"""
    data = request.get_json()
    backup_name = data.get("backup_name")
    if not backup_name:
        return jsonify({"success": False, "error": "Backup name required"}), 400

    result = ota_manager.rollback(backup_name)
    return jsonify(result)


@app.route("/api/admin/ota/update-cron", methods=["POST"])
def update_cron():
    """Update cron schedule for automatic updates"""
    data = request.get_json()
    schedule = data.get("schedule")
    if not schedule:
        return jsonify({"success": False, "error": "Schedule required"}), 400

    result = ota_manager.update_cron_schedule(schedule)
    return jsonify(result)


@app.route("/api/admin/ota/test-connection")
def test_git_connection():
    """Test Git connectivity"""
    return jsonify(ota_manager.test_git_connection())


@app.route("/api/admin/ota/history")
def get_update_history():
    """Get OTA update history"""
    return jsonify(ota_manager.get_update_history())


@app.route("/api/admin/ota/clean-cache", methods=["POST"])
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
def import_theme():
    """Import a theme from uploaded JSON"""
    try:
        theme_data = request.get_json()
        if theme_manager.import_theme(theme_data):
            return jsonify({"success": True, "message": "Theme imported successfully"})
        return jsonify({"success": False, "error": "Invalid theme format"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/themes/custom", methods=["POST"])
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
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/themes/custom/<theme_id>", methods=["DELETE"])
def delete_custom_theme(theme_id):
    """Delete a custom theme"""
    if theme_manager.delete_custom_theme(theme_id):
        return jsonify({"success": True, "message": "Theme deleted successfully"})
    return jsonify({"success": False, "error": "Theme not found or is built-in"}), 404


# Configuration endpoints
@app.route("/api/admin/config")
def get_config():
    """Get device configuration"""
    import socket

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
        # Fallback to localhost if can't determine IP
        config["network"] = {"ip_address": "localhost"}

    return jsonify(config)


@app.route("/api/admin/config", methods=["POST"])
def update_config():
    """Update device configuration"""
    data = request.get_json()

    # Update config file
    if not config_manager.update_config(data):
        return jsonify({"success": False, "error": "Failed to update config"}), 500

    # Also update .env file if PostHog credentials are provided
    if "posthog" in data:
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        env_lines = []

        # Read existing .env file if it exists
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                for line in f:
                    # Skip PostHog-related lines, we'll add them fresh
                    if not line.startswith(
                        ("POSTHOG_API_KEY=", "POSTHOG_PROJECT_ID=", "POSTHOG_HOST=")
                    ):
                        env_lines.append(line.rstrip())

        # Add PostHog configuration
        if data["posthog"].get("api_key"):
            env_lines.append(f"POSTHOG_API_KEY={data['posthog']['api_key']}")
        if data["posthog"].get("project_id"):
            env_lines.append(f"POSTHOG_PROJECT_ID={data['posthog']['project_id']}")
        if data["posthog"].get("host"):
            env_lines.append(f"POSTHOG_HOST={data['posthog']['host']}")

        # Write updated .env file
        with open(env_file, "w") as f:
            f.write("\n".join(env_lines) + "\n")

    return jsonify({"success": True})


@app.route("/api/admin/config/validate/posthog", methods=["POST"])
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
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Try to fetch project info to validate credentials
        test_url = f"{host}/api/projects/{project_id}/"
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                "valid": True,
                "message": "✅ PostHog connection successful!"
            })
        elif response.status_code == 401:
            return jsonify({
                "valid": False,
                "error": "❌ Invalid API key"
            }), 401
        elif response.status_code == 403:
            return jsonify({
                "valid": False,
                "error": "❌ API key doesn't have access to this project"
            }), 403
        elif response.status_code == 404:
            return jsonify({
                "valid": False,
                "error": "❌ Project not found. Check your Project ID"
            }), 404
        else:
            return jsonify({
                "valid": False,
                "error": f"❌ PostHog API error: {response.status_code}"
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            "valid": False,
            "error": "❌ Connection timeout. Check your network or host URL"
        }), 408
    except requests.exceptions.ConnectionError:
        return jsonify({
            "valid": False,
            "error": "❌ Could not connect to PostHog. Check the host URL"
        }), 503
    except Exception as e:
        return jsonify({
            "valid": False,
            "error": f"❌ Error testing connection: {str(e)}"
        }), 500


@app.route("/api/admin/config", methods=["DELETE"])
def delete_config():
    """Delete device configuration completely"""
    try:
        # Clear configuration from memory
        config = config_manager.get_config()
        if "posthog" in config:
            config["posthog"] = {}
            config_manager.update_config(config)

        # Clear .env file
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        env_lines = []

        # Read existing .env file if it exists and remove PostHog lines
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                for line in f:
                    # Skip PostHog-related lines
                    if not line.startswith(
                        ("POSTHOG_API_KEY=", "POSTHOG_PROJECT_ID=", "POSTHOG_HOST=")
                    ):
                        env_lines.append(line.rstrip())

        # Write updated .env file (essentially empty or with other configs)
        with open(env_file, "w") as f:
            if env_lines:
                f.write("\n".join(env_lines) + "\n")
            else:
                # Write empty placeholders
                f.write("# DataOrb configuration removed\n")
                f.write("POSTHOG_API_KEY=\n")
                f.write("POSTHOG_PROJECT_ID=\n")
                f.write("POSTHOG_HOST=\n")

        return jsonify(
            {"success": True, "message": "Configuration deleted successfully"}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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

# Serve React App for all other routes - This MUST be after all API and static routes
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path):
    """Serve the React application for all non-API routes"""
    # Don't serve API routes
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    
    # For all routes (including /config, /setup), serve index.html
    # This allows React Router to handle client-side routing
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    # Perform boot update check if enabled
    try:
        boot_result = ota_manager.perform_boot_update()
        if boot_result.get("error"):
            logger.warning(f"Boot update warning: {boot_result['error']}")
        elif boot_result.get("success"):
            logger.info("Boot update completed successfully")
    except Exception as e:
        logger.error(f"Boot update check failed: {e}")

    app.run(host="0.0.0.0", port=5000, debug=False)