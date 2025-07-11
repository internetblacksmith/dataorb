from flask import Flask, jsonify, send_from_directory, send_file, request
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from config_manager import ConfigManager
from ota_manager import OTAManager

load_dotenv()

# Configure Flask to serve React build files
app = Flask(__name__, static_folder='../frontend/build', static_url_path='')

# Enable CORS for API routes only
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# PostHog configuration
POSTHOG_API_KEY = os.getenv('POSTHOG_API_KEY')
POSTHOG_PROJECT_ID = os.getenv('POSTHOG_PROJECT_ID')
POSTHOG_HOST = os.getenv('POSTHOG_HOST', 'https://app.posthog.com')

# Initialize managers
config_manager = ConfigManager()
ota_manager = OTAManager(config_manager)

@app.route('/api/stats')
def get_stats():
    """Get basic PostHog statistics"""
    if not POSTHOG_API_KEY or not POSTHOG_PROJECT_ID:
        return jsonify({"error": "PostHog credentials not configured"})
    
    try:
        headers = {
            'Authorization': f'Bearer {POSTHOG_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Get events for last 24 hours
        events_url = f"{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/events"
        params = {
            'after': (datetime.now() - timedelta(days=1)).isoformat(),
            'limit': 100
        }
        
        response = requests.get(events_url, headers=headers, params=params)
        
        if response.status_code != 200:
            return jsonify({"error": f"PostHog API error: {response.status_code}"})
        
        events = response.json().get('results', [])
        
        # Calculate various metrics
        total_events = len(events)
        unique_users = len(set(event.get('distinct_id') for event in events))
        page_views = len([e for e in events if e.get('event') == '$pageview'])
        custom_events = total_events - page_views
        sessions = len(set(event.get('$session_id') for event in events if event.get('$session_id')))
        
        # Get recent events (last 10)
        recent_events = events[:10] if events else []
        
        # Calculate metrics for different time periods
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        events_last_hour = len([e for e in events if datetime.fromisoformat(e.get('timestamp', '').replace('Z', '+00:00')) > last_hour])
        
        all_metrics = {
            "events_24h": total_events,
            "unique_users_24h": unique_users,
            "page_views_24h": page_views,
            "custom_events_24h": custom_events,
            "sessions_24h": sessions,
            "events_1h": events_last_hour,
            "avg_events_per_user": round(total_events / unique_users, 1) if unique_users > 0 else 0,
            "recent_events": recent_events,
            "last_updated": datetime.now().isoformat()
        }
        
        return jsonify(all_metrics)
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch PostHog data: {str(e)}"})

@app.route('/api/metrics/available')
def get_available_metrics():
    """Get list of available metrics for configuration"""
    available_metrics = {
        "events_24h": {"label": "Events (24h)", "description": "Total events in last 24 hours"},
        "unique_users_24h": {"label": "Users (24h)", "description": "Unique users in last 24 hours"},
        "page_views_24h": {"label": "Page Views (24h)", "description": "Page view events in last 24 hours"},
        "custom_events_24h": {"label": "Custom Events (24h)", "description": "Non-pageview events in last 24 hours"},
        "sessions_24h": {"label": "Sessions (24h)", "description": "Unique sessions in last 24 hours"},
        "events_1h": {"label": "Events (1h)", "description": "Events in last hour"},
        "avg_events_per_user": {"label": "Avg Events/User", "description": "Average events per user (24h)"}
    }
    return jsonify(available_metrics)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# OTA Management API Routes
@app.route('/api/admin/ota/status')
def get_ota_status():
    """Get OTA status and information"""
    return jsonify(ota_manager.get_status())

@app.route('/api/admin/ota/check')
def check_for_updates():
    """Check for available updates"""
    return jsonify(ota_manager.check_for_updates())

@app.route('/api/admin/ota/update', methods=['POST'])
def update_system():
    """Pull latest updates"""
    return jsonify(ota_manager.pull_updates())

@app.route('/api/admin/ota/switch-branch', methods=['POST'])
def switch_branch():
    """Switch to a different branch"""
    data = request.get_json()
    branch = data.get('branch')
    
    if not branch:
        return jsonify({"success": False, "error": "Branch name is required"}), 400
    
    return jsonify(ota_manager.switch_branch(branch))

@app.route('/api/admin/ota/reset', methods=['POST'])
def reset_to_remote():
    """Hard reset to remote branch"""
    data = request.get_json()
    branch = data.get('branch')
    
    if not branch:
        return jsonify({"success": False, "error": "Branch name is required"}), 400
    
    return jsonify(ota_manager.reset_to_remote(branch))

@app.route('/api/admin/ota/config', methods=['GET', 'POST'])
def ota_config():
    """Get or update OTA configuration"""
    if request.method == 'GET':
        return jsonify(config_manager.get_section("ota"))
    
    data = request.get_json()
    if config_manager.update_section("ota", data):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to update OTA config"}), 500

@app.route('/api/admin/ota/backups')
def get_backups():
    """Get list of available backup tags"""
    return jsonify({"backups": ota_manager.get_backups()})

@app.route('/api/admin/ota/backup', methods=['POST'])
def create_backup():
    """Create a backup of current state"""
    return jsonify(ota_manager.create_backup())

@app.route('/api/admin/ota/rollback', methods=['POST'])
def rollback_to_backup():
    """Rollback to a specific backup"""
    data = request.get_json()
    backup_tag = data.get('backup_tag')
    
    if not backup_tag:
        return jsonify({"success": False, "error": "Backup tag is required"}), 400
    
    return jsonify(ota_manager.rollback_to_backup(backup_tag))

# Configuration API Routes
@app.route('/api/admin/config')
def get_config():
    """Get device configuration"""
    return jsonify(config_manager.get_config())

@app.route('/api/admin/config', methods=['POST'])
def update_config():
    """Update device configuration"""
    data = request.get_json()
    if config_manager.update_config(data):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to update config"}), 500


# Serve React App
@app.route('/')
def serve_react_app():
    """Serve the React application"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    """Serve static files from React build"""
    try:
        return send_from_directory(app.static_folder, path)
    except FileNotFoundError:
        # If file not found, serve index.html for React Router
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # Perform boot update check if enabled
    try:
        boot_result = ota_manager.perform_boot_update()
        if boot_result.get('error'):
            print(f"Boot update warning: {boot_result['error']}")
        elif boot_result.get('success'):
            print("Boot update completed successfully")
    except Exception as e:
        print(f"Boot update check failed: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)