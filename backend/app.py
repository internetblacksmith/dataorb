from flask import Flask, jsonify, send_from_directory, request, render_template
from flask_cors import CORS
import requests
import os
import logging
from datetime import datetime, timedelta, timezone
from config_manager import ConfigManager
from ota_manager import OTAManager
from themes import ThemeManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Flask to serve React build files and use templates
# Don't use static_url_path="" as it interferes with routing
app = Flask(
    __name__,
    static_folder="../frontend/build",
    static_url_path="/static-files",
    template_folder="templates",
)

CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize managers
config_manager = ConfigManager()
ota_manager = OTAManager(config_manager)
theme_manager = ThemeManager(config_manager)


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


def format_metric_object(value, label):
    """Format a metric as an object with label and value"""
    return {"label": label, "value": value}


def get_device_ip():
    """Get the device's IP address"""
    try:
        config = config_manager.get_config()
        network_status = config.get("network", {})
        return network_status.get("current_ip", "Unknown")
    except Exception:
        return "Unknown"


def get_demo_mode():
    """Check if running in demo mode"""
    config = config_manager.get_config()
    return config.get("demo_mode", False)


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
    """Check network connectivity and start WAP if disconnected"""
    import subprocess
    
    # Check if we have network connectivity
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
    POSTHOG_API_KEY, POSTHOG_PROJECT_ID, POSTHOG_HOST = get_posthog_config()
    if not POSTHOG_API_KEY or not POSTHOG_PROJECT_ID:
        return None, "PostHog credentials not configured"

    try:
        headers = {
            "Authorization": f"Bearer {POSTHOG_API_KEY}",
            "Content-Type": "application/json",
        }

        events_url = f"{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/events"
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
            # Return demo data if API fails
            return {
                "events_24h": 142,
                "unique_users_24h": 37,
                "page_views_24h": 89,
                "custom_events_24h": 53,
                "sessions_24h": 24,
                "events_1h": 8,
                "avg_events_per_user": 3.8,
                "demo_mode": True,
            }, None

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
        return None, str(e)


def fetch_classic_dashboard_stats():
    """Fetch and format stats specifically for Classic dashboard"""
    metrics, error = fetch_posthog_metrics()

    if error:
        return None, error

    config = config_manager.get_config()
    layout_config = config.get("display", {}).get("metrics", {}).get("classic", {})

    response = {"demo_mode": metrics.get("demo_mode", False), "device_ip": get_device_ip()}

    # Add positioned metrics with labels
    for position in ["top", "left", "right"]:
        if position in layout_config:
            metric_config = layout_config[position]
            if metric_config.get("enabled"):
                metric_type = metric_config.get("type")
                label = metric_config.get("label") or get_default_metric_label(metric_type)
                value = metrics.get(metric_type, 0)
                response[position] = format_metric_object(value, label)

    return response, None


def fetch_modern_dashboard_stats():
    """Fetch and format stats specifically for Modern dashboard"""
    metrics, error = fetch_posthog_metrics()

    if error:
        return None, error

    config = config_manager.get_config()
    layout_config = config.get("display", {}).get("metrics", {}).get("modern", {})

    response = {
        "demo_mode": metrics.get("demo_mode", False),
        "device_ip": get_device_ip(),
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
    }

    # Map positions to response keys
    position_map = {
        "top": "primary",
        "left": "secondaryLeft",
        "right": "secondaryRight",
        "mini1": "miniStat1",
        "mini2": "miniStat2",
        "mini3": "miniStat3",
    }

    for config_pos, response_key in position_map.items():
        if config_pos in layout_config:
            metric_config = layout_config[config_pos]
            if metric_config.get("enabled"):
                metric_type = metric_config.get("type")
                label = metric_config.get("label") or get_default_metric_label(metric_type)
                value = metrics.get(metric_type, 0)
                response[response_key] = format_metric_object(value, label)

    return response, None


def fetch_analytics_dashboard_stats():
    """Fetch and format stats specifically for Analytics dashboard"""
    metrics, error = fetch_posthog_metrics()

    if error:
        return None, error

    config = config_manager.get_config()
    layout_config = config.get("display", {}).get("metrics", {}).get("analytics", {})

    response = {
        "demo_mode": metrics.get("demo_mode", False),
        "device_ip": get_device_ip(),
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
    }

    # Add all Analytics positions
    for position in ["center", "top", "left", "right", "bottom", "stat1", "stat2", "stat3"]:
        if position in layout_config:
            metric_config = layout_config[position]
            if metric_config.get("enabled"):
                metric_type = metric_config.get("type")
                label = metric_config.get("label") or get_default_metric_label(metric_type)
                value = metrics.get(metric_type, 0)
                response[position] = format_metric_object(value, label)

    return response, None


def fetch_executive_dashboard_stats():
    """Fetch and format stats specifically for Executive dashboard"""
    metrics, error = fetch_posthog_metrics()

    if error:
        return None, error

    config = config_manager.get_config()
    layout_config = config.get("display", {}).get("metrics", {}).get("executive", {})

    response = {
        "demo_mode": metrics.get("demo_mode", False),
        "device_ip": get_device_ip(),
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "recent_events": metrics.get("recent_events", []),
    }

    # Map positions to response keys with camelCase
    position_map = {
        "north": "north",
        "east": "east",
        "south": "south",
        "west": "west",
        "northeast": "northEast",
        "southeast": "southEast",
        "southwest": "southWest",
        "northwest": "northWest",
    }

    for config_pos, response_key in position_map.items():
        if config_pos in layout_config:
            metric_config = layout_config[config_pos]
            if metric_config.get("enabled"):
                metric_type = metric_config.get("type")
                label = metric_config.get("label") or get_default_metric_label(metric_type)
                value = metrics.get(metric_type, 0)
                response[response_key] = format_metric_object(value, label)

    return response, None


@app.route("/api/stats/classic")
def get_classic_stats():
    """Get stats for Classic dashboard"""
    stats, error = fetch_classic_dashboard_stats()

    if error:
        if error == "NETWORK_ERROR":
            return jsonify({"error": "network_lost", "redirect": "/setup"}), 503
        return jsonify({"error": error}), 500

    return jsonify(stats)


@app.route("/api/stats/modern")
def get_modern_stats():
    """Get stats for Modern dashboard"""
    stats, error = fetch_modern_dashboard_stats()

    if error:
        if error == "NETWORK_ERROR":
            return jsonify({"error": "network_lost", "redirect": "/setup"}), 503
        return jsonify({"error": error}), 500

    return jsonify(stats)


@app.route("/api/stats/analytics")
def get_analytics_stats():
    """Get stats for Analytics dashboard"""
    stats, error = fetch_analytics_dashboard_stats()

    if error:
        if error == "NETWORK_ERROR":
            return jsonify({"error": "network_lost", "redirect": "/setup"}), 503
        return jsonify({"error": error}), 500

    return jsonify(stats)


@app.route("/api/stats/executive")
def get_executive_stats():
    """Get stats for Executive dashboard"""
    stats, error = fetch_executive_dashboard_stats()

    if error:
        if error == "NETWORK_ERROR":
            return jsonify({"error": "network_lost", "redirect": "/setup"}), 503
        return jsonify({"error": error}), 500

    return jsonify(stats)


@app.route("/api/stats")
def get_stats():
    """Get basic DataOrb statistics"""
    # Get optional layout parameter to determine which metrics to fetch
    layout = request.args.get("layout", None)

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
                jsonify({"error": "PostHog API error: 403 - Missing permissions or wrong project"}),
                403,
            )
        elif response.status_code != 200:
            # If PostHog API is having issues, return demo data
            if response.status_code == 500:
                return jsonify(
                    {
                        "events_24h": 142,
                        "unique_users_24h": 37,
                        "page_views_24h": 89,
                        "custom_events_24h": 53,
                        "sessions_24h": 24,
                        "events_1h": 8,
                        "avg_events_per_user": 3.8,
                        "recent_events": [
                            {
                                "event": "$pageview",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                            {
                                "event": "button_click",
                                "timestamp": (
                                    datetime.now(timezone.utc) - timedelta(minutes=5)
                                ).isoformat(),
                            },
                            {
                                "event": "$pageview",
                                "timestamp": (
                                    datetime.now(timezone.utc) - timedelta(minutes=12)
                                ).isoformat(),
                            },
                        ],
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                        "demo_mode": True,
                    }
                )
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

        # Create all metrics dictionary
        all_metrics = {
            "events_24h": events_24h,
            "unique_users_24h": unique_users,
            "page_views_24h": page_views,
            "custom_events_24h": custom_events,
            "sessions_24h": sessions,
            "events_1h": events_1h,
            "avg_events_per_user": avg_events_per_user,
        }

        # Determine which metrics to include based on layout
        if layout:
            # For backwards compatibility with old endpoints
            # Simply return all metrics with recent events
            response_data = {
                **all_metrics,
                "recent_events": recent_events,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        else:
            # No layout specified, return all metrics (backward compatibility)
            response_data = {
                **all_metrics,
                "recent_events": recent_events,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)})


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
        return jsonify({"error": str(e)}), 500


@app.route("/api/network/connect", methods=["POST"])
def connect_network():
    """Connect to a WiFi network"""
    import subprocess
    
    data = request.get_json()
    ssid = data.get("ssid")
    password = data.get("password")
    
    if not ssid:
        return jsonify({"success": False, "error": "SSID is required"}), 400
        
    try:
        # Create wpa_supplicant configuration
        wpa_conf = f"""network={{
    ssid="{ssid}"
    psk="{password}"
}}"""
        
        # Write to wpa_supplicant.conf
        subprocess.run(
            ["sudo", "bash", "-c", f"echo '{wpa_conf}' >> /etc/wpa_supplicant/wpa_supplicant.conf"],
            check=True,
            timeout=5
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
        return jsonify({"success": False, "error": str(e)}), 500


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
            "ap_password": "dataorb123" if ap_mode else None,
            
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
            return jsonify({"valid": True, "message": "✅ PostHog connection successful!"})
        elif response.status_code == 401:
            return jsonify({"valid": False, "error": "❌ Invalid API key"}), 401
        elif response.status_code == 403:
            return (
                jsonify(
                    {"valid": False, "error": "❌ API key doesn't have access to this project"}
                ),
                403,
            )
        elif response.status_code == 404:
            return (
                jsonify({"valid": False, "error": "❌ Project not found. Check your Project ID"}),
                404,
            )
        else:
            return (
                jsonify({"valid": False, "error": f"❌ PostHog API error: {response.status_code}"}),
                response.status_code,
            )

    except requests.exceptions.Timeout:
        return (
            jsonify(
                {"valid": False, "error": "❌ Connection timeout. Check your network or host URL"}
            ),
            408,
        )
    except requests.exceptions.ConnectionError:
        return (
            jsonify(
                {"valid": False, "error": "❌ Could not connect to PostHog. Check the host URL"}
            ),
            503,
        )
    except Exception as e:
        return jsonify({"valid": False, "error": f"❌ Error testing connection: {str(e)}"}), 500


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

        return jsonify({"success": True, "message": "Configuration deleted successfully"})
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
            logger.warning(f"Boot update warning: {boot_result['error']}")
        elif boot_result.get("success"):
            logger.info("Boot update completed successfully")
    except Exception as e:
        logger.error(f"Boot update check failed: {e}")

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
