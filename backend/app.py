from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import requests
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from config_manager import ConfigManager
from ota_manager import OTAManager

load_dotenv()

# Configure Flask to serve React build files
app = Flask(__name__, static_folder="../frontend/build", static_url_path="")

CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize managers
config_manager = ConfigManager()
ota_manager = OTAManager(config_manager)

# Load PostHog configuration from config file or environment
def get_posthog_config():
    """Get PostHog configuration from config file or environment variables"""
    config = config_manager.get_config()
    
    # Try to get from saved config first
    api_key = config.get("posthog", {}).get("api_key") or os.getenv("POSTHOG_API_KEY")
    project_id = config.get("posthog", {}).get("project_id") or os.getenv("POSTHOG_PROJECT_ID")
    host = config.get("posthog", {}).get("host") or os.getenv("POSTHOG_HOST", "https://app.posthog.com")
    
    return api_key, project_id, host


@app.route("/api/stats")
def get_stats():
    """Get basic PostHog statistics"""
    # Get current PostHog configuration
    POSTHOG_API_KEY, POSTHOG_PROJECT_ID, POSTHOG_HOST = get_posthog_config()
    
    if not POSTHOG_API_KEY or not POSTHOG_PROJECT_ID:
        return jsonify({"error": "PostHog credentials not configured"})

    try:
        headers = {
            "Authorization": f"Bearer {POSTHOG_API_KEY}",
            "Content-Type": "application/json",
        }

        # Get events for last 24 hours
        events_url = f"{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/events"
        params = {
            "after": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "limit": "100",
        }

        response = requests.get(events_url, headers=headers, params=params)

        if response.status_code == 401:
            return jsonify({"error": "PostHog API error: 401 - Invalid API key"}), 401
        elif response.status_code == 403:
            return jsonify({"error": "PostHog API error: 403 - Missing permissions or wrong project"}), 403
        elif response.status_code != 200:
            return jsonify({"error": f"PostHog API error: {response.status_code}"}), response.status_code

        data = response.json()
        events = data.get("results", [])

        # Calculate statistics
        events_24h = len(events)
        unique_users = len(set(e.get("distinct_id", "") for e in events))
        page_views = len([e for e in events if e.get("event") == "$pageview"])
        custom_events = len([e for e in events if e.get("event") not in ["$pageview", "$pageleave"]])
        
        # Get sessions count (unique session IDs)
        sessions = len(set(e.get("properties", {}).get("$session_id", "") for e in events if e.get("properties", {}).get("$session_id")))
        
        # Get events from last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        events_1h = len([e for e in events if datetime.fromisoformat(e.get("timestamp", "").replace("Z", "+00:00")) > one_hour_ago])
        
        # Calculate average events per user
        avg_events_per_user = round(events_24h / unique_users, 1) if unique_users > 0 else 0

        # Get recent events for activity feed
        recent_events = []
        for event in events[:10]:  # Last 10 events
            recent_events.append({
                "event": event.get("event", "Unknown"),
                "user": event.get("distinct_id", "Anonymous")[:8],
                "timestamp": event.get("timestamp", ""),
                "properties": event.get("properties", {}),
            })

        return jsonify({
            "events_24h": events_24h,
            "unique_users_24h": unique_users,
            "page_views_24h": page_views,
            "custom_events_24h": custom_events,
            "sessions_24h": sessions,
            "events_1h": events_1h,
            "avg_events_per_user": avg_events_per_user,
            "recent_events": recent_events,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        })

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})


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
def perform_ota_update():
    """Perform OTA update"""
    data = request.get_json() or {}
    force = data.get("force", False)
    return jsonify(ota_manager.perform_update(force=force))


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
            return jsonify({"success": False, "error": "Failed to update OTA config"}), 500


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


@app.route("/api/admin/ota/rollback", methods=["POST"])
def rollback_update():
    """Rollback to a previous backup"""
    data = request.get_json() or {}
    backup_name = data.get("backup_name")
    return jsonify(ota_manager.rollback(backup_name))


@app.route("/api/admin/ota/backups")
def list_backups():
    """List available backups"""
    return jsonify(ota_manager.list_backups())


@app.route("/api/admin/ota/logs")
def get_ota_logs():
    """Get OTA update logs"""
    lines = request.args.get("lines", 100, type=int)
    return jsonify(ota_manager.get_logs(lines))


@app.route("/api/admin/ota/restart", methods=["POST"])
def restart_services():
    """Restart application services"""
    return jsonify(ota_manager.restart_services())


@app.route("/api/admin/ota/reboot", methods=["POST"])
def reboot_system():
    """Reboot the system"""
    data = request.get_json() or {}
    delay = data.get("delay", 10)
    return jsonify(ota_manager.reboot_system(delay))


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


@app.route("/api/admin/ota/disk-usage")
def get_disk_usage():
    """Get disk usage information"""
    return jsonify(ota_manager.get_disk_usage())


@app.route("/api/admin/ota/clean-cache", methods=["POST"])
def clean_cache():
    """Clean temporary files and caches"""
    return jsonify(ota_manager.clean_cache())


# Configuration endpoints
@app.route("/api/admin/config")
def get_config():
    """Get device configuration"""
    return jsonify(config_manager.get_config())


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
                    if not line.startswith(("POSTHOG_API_KEY=", "POSTHOG_PROJECT_ID=", "POSTHOG_HOST=")):
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


# Serve React App
@app.route("/")
def serve_react_app():
    """Serve the React application"""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/config")
def serve_config_page():
    """Serve the configuration page"""
    config_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PostHog Configuration</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #0a0e27;
                color: white;
                min-height: 100vh;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
            }
            h1 {
                color: #1d4aff;
                text-align: center;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                color: #94a3b8;
            }
            input, select {
                width: 100%;
                padding: 10px;
                border: 1px solid #334155;
                border-radius: 5px;
                background: #1e293b;
                color: white;
                font-size: 16px;
            }
            button {
                background: #1d4aff;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
            }
            button:hover {
                background: #1639cc;
            }
            .success {
                background: #10b981;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                text-align: center;
                display: none;
            }
            .error {
                background: #ef4444;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                text-align: center;
                display: none;
            }
            .info {
                background: #1e293b;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .instructions {
                background: #1e293b;
                border-left: 4px solid #1d4aff;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .instructions h3 {
                color: #1d4aff;
                margin-top: 0;
            }
            .instructions ol {
                margin: 10px 0;
                padding-left: 20px;
            }
            .instructions li {
                margin: 8px 0;
                line-height: 1.5;
            }
            .instructions code {
                background: #0a0e27;
                padding: 2px 6px;
                border-radius: 3px;
                color: #10b981;
            }
            .error-401 {
                background: #7f1d1d;
                border: 1px solid #ef4444;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .current-status {
                margin-top: 20px;
                padding: 15px;
                background: #1e293b;
                border-radius: 5px;
            }
            .status-item {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
            }
            .status-value {
                color: #10b981;
            }
            .status-value.not-configured {
                color: #ef4444;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🦔 PostHog Configuration</h1>
            
            <div id="success" class="success">
                Configuration saved! 
                <br><span style="font-size: 14px;">✨ All dashboard displays will reload automatically...</span>
                <br><span style="font-size: 12px;">Redirecting in 2 seconds...</span>
            </div>
            <div id="error" class="error">Error saving configuration</div>
            
            <div class="info">
                <p>Configure your PostHog API credentials to start tracking analytics.</p>
            </div>
            
            <div class="instructions">
                <h3>📖 How to Get Your PostHog API Credentials (2025 Version)</h3>
                <ol>
                    <li><strong>Sign in to PostHog:</strong> Go to <a href="https://app.posthog.com" target="_blank" style="color: #1d4aff;">app.posthog.com</a> or <a href="https://eu.posthog.com" target="_blank" style="color: #1d4aff;">eu.posthog.com</a></li>
                    <li><strong>Create Your Personal API Key:</strong>
                        <ul style="margin-top: 5px;">
                            <li>Click your <strong>avatar icon</strong> (bottom left corner)</li>
                            <li>Click the <strong>gear icon</strong> to go to "Account settings"</li>
                            <li>In "My settings", go to the <strong>"Personal API Keys"</strong> tab</li>
                            <li>Click <code>+ Create personal API key</code></li>
                            <li>Give it a label like "Pi Dashboard"</li>
                            <li><strong style="color: #fbbf24;">⚠️ Organization & project access:</strong>
                                <ul style="margin-top: 5px;">
                                    <li>Select <strong>"Current project only"</strong> or your specific project</li>
                                    <li>Do NOT select "All projects" - it may cause permission issues</li>
                                </ul>
                            </li>
                            <li><strong style="color: #10b981;">Select Scopes:</strong>
                                <ul style="margin-top: 5px;">
                                    <li>✅ Enable <strong>Full access</strong> (recommended)</li>
                                    <li>💡 PostHog's API requires broad permissions even for read-only operations</li>
                                </ul>
                            </li>
                            <li>Click <strong>Create key</strong></li>
                            <li><strong style="color: #fbbf24;">⚠️ COPY IMMEDIATELY!</strong> You won't see it again!</li>
                            <li>The key starts with <code>phx_</code></li>
                        </ul>
                    </li>
                    <li><strong>Get Your Project ID:</strong>
                        <ul style="margin-top: 5px;">
                            <li>Go to <code>Project Settings</code> (gear icon in sidebar)</li>
                            <li>Find <code>Project ID</code> under General tab</li>
                            <li>Copy the numeric ID (e.g., <code>12345</code>)</li>
                        </ul>
                    </li>
                    <li><strong>Choose Your Host:</strong>
                        <ul style="margin-top: 5px;">
                            <li><strong>US Cloud:</strong> <code>https://app.posthog.com</code></li>
                            <li><strong>EU Cloud:</strong> <code>https://eu.posthog.com</code></li>
                            <li><strong>Self-hosted:</strong> Your instance URL</li>
                        </ul>
                    </li>
                </ol>
                
                <div style="background: #0a0e27; padding: 15px; border-radius: 5px; margin-top: 15px;">
                    <strong style="color: #fbbf24;">⚠️ Important Notes:</strong>
                    <ul style="margin: 10px 0 0 20px; padding: 0;">
                        <li><strong>Security:</strong> Only grant the minimum scopes needed (Read Events, Insights, Projects)</li>
                        <li><strong>Key Format:</strong> Personal keys start with <code>phx_</code>, Project keys with <code>phc_</code></li>
                        <li><strong>Copy Immediately:</strong> You can't view the key again after creation!</li>
                        <li><strong>Error 401:</strong> Usually means wrong key, missing scopes, or wrong host (US vs EU)</li>
                        <li><strong>Rate Limits:</strong> 240 requests/minute, 1200/hour for analytics endpoints</li>
                        <li><strong>Best Practice:</strong> Use Personal API Keys (more secure than Project keys)</li>
                    </ul>
                </div>
                
                <div style="background: #1a1f3a; padding: 15px; border-radius: 5px; margin-top: 15px; border: 1px solid #1d4aff;">
                    <strong style="color: #1d4aff;">🔑 Required Settings Summary:</strong>
                    <ul style="margin: 10px 0 0 20px; padding: 0; color: #94a3b8;">
                        <li><strong>Organization & project access:</strong> <code style="color: #10b981;">Current project only</code></li>
                        <li><strong>Scopes:</strong> <code style="color: #10b981;">Full access</code></li>
                        <li><strong>Key format:</strong> Starts with <code style="color: #10b981;">phx_</code></li>
                    </ul>
                    <p style="margin-top: 10px; color: #fbbf24; font-size: 14px;">
                        ⚠️ <strong>Important:</strong> PostHog's API requires full access even for read-only operations due to how Personal API keys work.
                    </p>
                </div>
            </div>
            
            <div id="error401" class="error-401" style="display: none;">
                <strong>🔴 Authentication Error (401)</strong><br>
                Your API key is invalid or expired. Please check:
                <ul style="margin: 10px 0 0 20px;">
                    <li>The API key is copied correctly (no extra spaces)</li>
                    <li>The key hasn't been deleted or regenerated</li>
                    <li>You're using the correct host URL</li>
                    <li>The Project ID matches your PostHog project</li>
                </ul>
            </div>
            
            <div id="error403" class="error-401" style="display: none;">
                <strong>🔴 Permission Error (403)</strong><br>
                Your API key doesn't have the required permissions. Please check:
                <ul style="margin: 10px 0 0 20px;">
                    <li><strong>Organization & project access:</strong> Make sure you selected your project (not "All projects")</li>
                    <li><strong>Project ID:</strong> Verify the Project ID matches the project you granted access to</li>
                    <li><strong>Scopes:</strong> Ensure these are enabled with Read access:
                        <ul style="margin-top: 5px;">
                            <li>Event definition - Read</li>
                            <li>Insight - Read</li>
                            <li>Project - Read</li>
                        </ul>
                    </li>
                    <li><strong>Host URL:</strong> Confirm you're using the right host (US vs EU)</li>
                </ul>
            </div>
            
            <div class="current-status">
                <h3>Current Status</h3>
                <div id="status">Loading...</div>
            </div>
            
            <form id="configForm">
                <div class="form-group">
                    <label for="apiKey">PostHog API Key *</label>
                    <input type="text" id="apiKey" name="apiKey" required 
                           placeholder="phx_xxxxxxxxxxxxxxxx">
                </div>
                
                <div class="form-group">
                    <label for="projectId">Project ID *</label>
                    <input type="text" id="projectId" name="projectId" required 
                           placeholder="1234">
                </div>
                
                <div class="form-group">
                    <label for="host">PostHog Host</label>
                    <select id="host" name="host">
                        <option value="https://app.posthog.com">PostHog Cloud (US)</option>
                        <option value="https://eu.posthog.com">PostHog Cloud (EU)</option>
                        <option value="custom">Custom/Self-hosted</option>
                    </select>
                    <input type="text" id="customHost" name="customHost" 
                           placeholder="https://your-posthog-instance.com" 
                           style="display:none; margin-top:10px;">
                </div>
                
                <button type="submit">Save Configuration</button>
            </form>
        </div>
        
        <script>
            // Check for errors from dashboard
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('error') === '401') {
                document.getElementById('error401').style.display = 'block';
            } else if (urlParams.get('error') === '403') {
                document.getElementById('error403').style.display = 'block';
            }
            
            // Load current configuration
            async function loadConfig() {
                try {
                    const response = await fetch('/api/admin/config');
                    const data = await response.json();
                    
                    // Check PostHog configuration
                    const statusDiv = document.getElementById('status');
                    if (data.posthog?.api_key) {
                        statusDiv.innerHTML = `
                            <div class="status-item">
                                <span>API Key:</span>
                                <span class="status-value">Configured ✓</span>
                            </div>
                            <div class="status-item">
                                <span>Project ID:</span>
                                <span class="status-value">${data.posthog.project_id || 'Not set'}</span>
                            </div>
                            <div class="status-item">
                                <span>Host:</span>
                                <span class="status-value">${data.posthog.host || 'https://app.posthog.com'}</span>
                            </div>
                        `;
                        
                        // Pre-fill form
                        document.getElementById('apiKey').value = data.posthog.api_key;
                        document.getElementById('projectId').value = data.posthog.project_id || '';
                        
                        const host = data.posthog.host || 'https://app.posthog.com';
                        if (host === 'https://app.posthog.com' || host === 'https://eu.posthog.com') {
                            document.getElementById('host').value = host;
                        } else {
                            document.getElementById('host').value = 'custom';
                            document.getElementById('customHost').style.display = 'block';
                            document.getElementById('customHost').value = host;
                        }
                    } else {
                        statusDiv.innerHTML = `
                            <div class="status-item">
                                <span>API Key:</span>
                                <span class="status-value not-configured">Not configured ✗</span>
                            </div>
                        `;
                    }
                } catch (err) {
                    console.error('Error loading config:', err);
                }
            }
            
            // Handle host selection
            document.getElementById('host').addEventListener('change', (e) => {
                const customHost = document.getElementById('customHost');
                if (e.target.value === 'custom') {
                    customHost.style.display = 'block';
                    customHost.required = true;
                } else {
                    customHost.style.display = 'none';
                    customHost.required = false;
                }
            });
            
            // Handle form submission
            document.getElementById('configForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                let host = formData.get('host');
                if (host === 'custom') {
                    host = formData.get('customHost');
                }
                
                const config = {
                    posthog: {
                        api_key: formData.get('apiKey'),
                        project_id: formData.get('projectId'),
                        host: host
                    }
                };
                
                try {
                    const response = await fetch('/api/admin/config', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(config)
                    });
                    
                    if (response.ok) {
                        document.getElementById('success').style.display = 'block';
                        document.getElementById('error').style.display = 'none';
                        
                        // Send reload signal to all dashboard pages
                        localStorage.setItem('posthog_config_updated', Date.now().toString());
                        
                        // Also try to reload any other open dashboard pages using broadcast channel
                        if (window.BroadcastChannel) {
                            const channel = new BroadcastChannel('posthog_config');
                            channel.postMessage({ action: 'reload' });
                            channel.close();
                        }
                        
                        // Redirect to dashboard after 2 seconds
                        setTimeout(() => {
                            window.location.href = '/';
                        }, 2000);
                    } else {
                        throw new Error('Failed to save configuration');
                    }
                } catch (err) {
                    document.getElementById('error').style.display = 'block';
                    document.getElementById('success').style.display = 'none';
                    console.error('Error saving config:', err);
                }
            });
            
            // Load config on page load
            loadConfig();
        </script>
    </body>
    </html>
    '''
    return config_html


@app.route("/<path:path>")
def serve_static_files(path):
    """Serve static files from React build"""
    try:
        return send_from_directory(app.static_folder, path)
    except FileNotFoundError:
        # If file not found, serve index.html for React Router
        return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    # Perform boot update check if enabled
    try:
        boot_result = ota_manager.perform_boot_update()
        if boot_result.get("error"):
            print(f"Boot update warning: {boot_result['error']}")
        elif boot_result.get("success"):
            print("Boot update completed successfully")
    except Exception as e:
        print(f"Boot update check failed: {e}")

    app.run(host="0.0.0.0", port=5000, debug=False)