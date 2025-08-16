#!/bin/bash

# DataOrb Display Kiosk Mode Startup Script
# This script starts the integrated Flask app and opens Chrome in kiosk mode

# Wait for network setup (managed by network service)
echo "Waiting for network setup..."
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
NETWORK_BOOT_SCRIPT="${SCRIPT_DIR}/network-boot.py"

# Wait for network service to complete setup
sleep 30

# Check network status
NETWORK_STATUS=$(python3 "$NETWORK_BOOT_SCRIPT" status 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "Network status: $NETWORK_STATUS"
else
    echo "Network status check failed, continuing anyway..."
fi

# Set display
export DISPLAY=:0

# Build React frontend first
echo "Building React frontend..."
cd /home/pi/pi-analytics-dashboard/frontend
npm install
npm run build

# Start the integrated Flask app (serves both API and React)
echo "Starting DataOrb integrated server..."
cd /home/pi/pi-analytics-dashboard/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py &
APP_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 15

# Configure Chrome for kiosk mode
echo "Starting Chrome in kiosk mode..."

# Remove Chrome crash flags
sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/Default/Preferences
sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences

# Start Chrome in kiosk mode
chromium-browser \
  --kiosk \
  --no-first-run \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-translate \
  --disable-features=TranslateUI \
  --disable-ipc-flooding-protection \
  --disable-background-timer-throttling \
  --disable-backgrounding-occluded-windows \
  --disable-renderer-backgrounding \
  --disable-field-trial-config \
  --disable-back-forward-cache \
  --disable-backgrounding-occluded-windows \
  --disable-features=VizDisplayCompositor \
  --start-fullscreen \
  --window-position=0,0 \
  --window-size=480,480 \
  --user-data-dir=/tmp/chrome-kiosk \
  http://localhost:5000

# Cleanup on exit
trap "kill $APP_PID" EXIT