#!/bin/bash

# Install systemd service for PostHog Pi network management
# This service handles network setup on boot and switches between AP and normal mode

SERVICE_NAME="posthog-pi-network"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing PostHog Pi Network Service..."

# Create systemd service file
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=PostHog Pi Network Manager
After=network.target
Wants=network.target

[Service]
Type=forking
ExecStart=/usr/bin/python3 ${SCRIPT_DIR}/network-boot.py setup
ExecStartPost=/bin/sleep 5
ExecStartPost=/usr/bin/python3 ${SCRIPT_DIR}/network-boot.py monitor
User=root
Group=root
Restart=on-failure
RestartSec=10
TimeoutStartSec=300
StandardOutput=journal
StandardError=journal

# Environment variables
Environment=PYTHONUNBUFFERED=1
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
WorkingDirectory=${PROJECT_DIR}

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
sudo chmod 644 "$SERVICE_FILE"

# Create log directory
sudo mkdir -p /var/log
sudo touch /var/log/posthog-pi-network.log
sudo chmod 666 /var/log/posthog-pi-network.log

# Reload systemd
sudo systemctl daemon-reload

# Enable the service
sudo systemctl enable "$SERVICE_NAME"

echo "PostHog Pi Network Service installed successfully!"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "The service will automatically start on boot and manage network connectivity."
echo "It will start in AP mode if no network is configured or available."