#!/usr/bin/env python3
"""
PostHog Pi - Integrated Flask Application
Serves both the API and React frontend from a single server
"""

# Import the Flask app from backend
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import app

if __name__ == '__main__':
    print("Starting PostHog Pi integrated server...")
    print("API endpoints available at /api/*")
    print("React app served at /")
    print("Server running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)