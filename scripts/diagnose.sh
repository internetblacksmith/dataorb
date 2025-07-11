#!/bin/bash

# PostHog Pi Diagnostic Script
# Run this script to diagnose display issues

echo "🔍 PostHog Pi Diagnostic Tool"
echo "================================="
echo

# Check system info
echo "📋 System Information:"
echo "Date: $(date)"
echo "User: $(whoami)"
echo "Home: $HOME"
echo "Current directory: $(pwd)"
echo "Display: $DISPLAY"
echo

# Check if PostHog Pi is installed
INSTALL_DIR="$HOME/posthog_pi"
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ PostHog Pi not found at $INSTALL_DIR"
    exit 1
fi

echo "✅ PostHog Pi found at $INSTALL_DIR"
echo

# Check systemd services
echo "🔧 Service Status:"
systemctl --user is-active posthog-display.service 2>/dev/null || echo "User service not found, checking system service..."
sudo systemctl is-active posthog-display.service 2>/dev/null || echo "❌ posthog-display.service not active"

sudo systemctl is-active lightdm 2>/dev/null || echo "❌ lightdm not active"
echo

# Check if Flask server is running
echo "🌐 Network Connectivity:"
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "✅ Flask server is responding at http://localhost:5000"
else
    echo "❌ Flask server not responding at http://localhost:5000"
fi
echo

# Check processes
echo "🔍 Running Processes:"
ps aux | grep -E "(python|chromium|flask)" | grep -v grep || echo "No Python/Chromium processes found"
echo

# Check if build files exist
echo "📁 Build Files:"
if [ -d "$INSTALL_DIR/frontend/build" ]; then
    echo "✅ React build directory exists"
    ls -la "$INSTALL_DIR/frontend/build/" | head -5
else
    echo "❌ React build directory missing"
fi
echo

# Check configuration
echo "⚙️ Configuration:"
if [ -f "$INSTALL_DIR/backend/device_config.json" ]; then
    echo "✅ Configuration file exists"
    echo "Display config:"
    cat "$INSTALL_DIR/backend/device_config.json" | grep -A 5 '"display"' || echo "No display config found"
else
    echo "❌ Configuration file missing"
fi
echo

# Check logs
echo "📝 Recent Logs:"
echo "--- System journal (last 20 lines) ---"
sudo journalctl -u posthog-display.service --no-pager -n 20 || echo "No service logs found"
echo

echo "--- Chromium logs ---"
if [ -f "$HOME/.config/chromium/chrome_debug.log" ]; then
    tail -10 "$HOME/.config/chromium/chrome_debug.log"
else
    echo "No Chromium logs found"
fi
echo

# Check X11/display
echo "🖥️ Display Information:"
echo "DISPLAY variable: $DISPLAY"
if command -v xset >/dev/null 2>&1; then
    xset q | head -3 || echo "Cannot query X server"
else
    echo "xset not available"
fi
echo

# Manual test suggestions
echo "🛠️ Manual Tests to Try:"
echo "1. Test Flask server manually:"
echo "   cd $INSTALL_DIR/backend && source venv/bin/activate && python3 app.py"
echo
echo "2. Test Chrome manually:"
echo "   DISPLAY=:0 chromium-browser --kiosk http://localhost:5000"
echo
echo "3. Check service logs:"
echo "   sudo journalctl -u posthog-display.service -f"
echo
echo "4. Restart services:"
echo "   sudo systemctl restart posthog-display.service"
echo "   sudo systemctl restart lightdm"
echo

echo "📞 If problems persist, please share this diagnostic output for support."