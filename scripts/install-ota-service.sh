#!/bin/bash

# Install PostHog Pi OTA Update Service
# This script installs the systemd service for boot-time OTA updates

set -e

# Configuration
SERVICE_NAME="posthog-pi-ota"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
USER="$(whoami)"

echo "Installing PostHog Pi OTA Update Service..."
echo "Project directory: $PROJECT_DIR"
echo "User: $USER"

# Create log directory
sudo mkdir -p /var/log/posthog-pi
sudo chown $USER:$USER /var/log/posthog-pi

# Copy service file with correct paths
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=PostHog Pi OTA Update Service
After=network.target
Wants=network.target

[Service]
Type=oneshot
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/scripts/boot-update.py
StandardOutput=journal
StandardError=journal
TimeoutSec=300

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

echo "✅ PostHog Pi OTA Update Service installed successfully!"
echo
echo "Service management commands:"
echo "  Check status: sudo systemctl status $SERVICE_NAME"
echo "  View logs:    sudo journalctl -u $SERVICE_NAME"
echo "  Run now:      sudo systemctl start $SERVICE_NAME"
echo "  Disable:      sudo systemctl disable $SERVICE_NAME"
echo
echo "The service will automatically run on boot to check for updates."