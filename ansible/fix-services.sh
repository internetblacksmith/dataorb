#!/bin/bash

# Fix missing services on Pi

echo "Creating systemd services..."

# Create Flask backend service
sudo tee /etc/systemd/system/posthog-backend.service > /dev/null << 'EOF'
[Unit]
Description=PostHog Pi Analytics Dashboard Backend
After=network.target

[Service]
Type=simple
User=pianalytics
WorkingDirectory=/home/pianalytics/pi_analytics_dashboard/backend
Environment="PATH=/home/pianalytics/pi_analytics_dashboard/backend/venv/bin:/usr/bin:/bin"
ExecStart=/home/pianalytics/pi_analytics_dashboard/backend/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create kiosk display service  
sudo tee /etc/systemd/system/posthog-display.service > /dev/null << 'EOF'
[Unit]
Description=PostHog Pi Analytics Dashboard Display
After=network.target posthog-backend.service
Wants=posthog-backend.service

[Service]
Type=simple
User=pianalytics
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/pianalytics/.Xauthority"
ExecStartPre=/bin/sleep 10
ExecStart=/home/pianalytics/pi_analytics_dashboard/scripts/start-kiosk.sh
Restart=always
RestartSec=10

[Install]
WantedBy=graphical.target
EOF

# Create the kiosk startup script
cat > /home/pianalytics/pi_analytics_dashboard/scripts/start-kiosk.sh << 'EOF'
#!/bin/bash

# Kill any existing chromium processes
killall chromium-browser 2>/dev/null || true

# Wait for Flask backend to be ready
while ! curl -s http://localhost:5000/api/health > /dev/null; do
    echo "Waiting for backend..."
    sleep 2
done

# Start X server if not running
if ! pgrep -x "Xorg" > /dev/null; then
    xinit /usr/bin/chromium-browser \
        --kiosk \
        --noerrdialogs \
        --disable-infobars \
        --disable-translate \
        --no-first-run \
        --fast \
        --fast-start \
        --disable-features=TranslateUI \
        --window-size=480,480 \
        --window-position=0,0 \
        http://localhost:5000 \
        -- -nocursor &
else
    # X is already running, just start chromium
    DISPLAY=:0 chromium-browser \
        --kiosk \
        --noerrdialogs \
        --disable-infobars \
        --disable-translate \
        --no-first-run \
        --fast \
        --fast-start \
        --disable-features=TranslateUI \
        --window-size=480,480 \
        --window-position=0,0 \
        http://localhost:5000 &
fi
EOF

# Make kiosk script executable
chmod +x /home/pianalytics/pi_analytics_dashboard/scripts/start-kiosk.sh

# Create scripts directory if it doesn't exist
mkdir -p /home/pianalytics/pi_analytics_dashboard/scripts

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
echo "Starting services..."
sudo systemctl enable posthog-backend
sudo systemctl start posthog-backend

echo "Waiting for backend to start..."
sleep 5

sudo systemctl enable posthog-display
sudo systemctl start posthog-display

# Check status
echo ""
echo "Service status:"
echo "---------------"
sudo systemctl status posthog-backend --no-pager | head -10
echo ""
sudo systemctl status posthog-display --no-pager | head -10

echo ""
echo "To check logs:"
echo "  sudo journalctl -u posthog-backend -f"
echo "  sudo journalctl -u posthog-display -f"