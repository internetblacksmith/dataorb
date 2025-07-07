from flask import Flask, jsonify, send_from_directory, send_file
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

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
        
        return jsonify({
            "events_24h": len(events),
            "unique_users_24h": len(set(event.get('distinct_id') for event in events)),
            "page_views_24h": len([e for e in events if e.get('event') == '$pageview']),
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch PostHog data: {str(e)}"})

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

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
    app.run(host='0.0.0.0', port=5000, debug=False)