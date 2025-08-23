#!/bin/bash

# Quick LCD Installation Script for Fresh Raspberry Pi
# Installs and configures LCD display (HyperPixel or Waveshare) without full playbook
# Mirrors the exact process from the ansible playbook

set -e

echo "========================================="
echo "Quick LCD Installation for Raspberry Pi"
echo "========================================="
echo "This script installs LCD display support on a fresh SD card"
echo "Supports: HyperPixel Round and Waveshare 3.4\" HDMI"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Require sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo $0"
    exit 1
fi

# =======================
# Configuration
# =======================
echo "=== Configuration ==="
echo "1) HyperPixel 2.1 Round (480x480)"
echo "2) Waveshare 3.4\" HDMI (800x800)"
echo ""
read -p "Select display type (1-2): " -n 1 -r
echo ""

if [ "$REPLY" = "1" ]; then
    DISPLAY_TYPE="hyperpixel_round"
    DISPLAY_WIDTH=480
    DISPLAY_HEIGHT=480
    echo "Selected: HyperPixel Round"
elif [ "$REPLY" = "2" ]; then
    DISPLAY_TYPE="waveshare_34_hdmi"
    DISPLAY_WIDTH=800
    DISPLAY_HEIGHT=800
    echo "Selected: Waveshare 3.4\" HDMI"
else
    echo "Invalid selection"
    exit 1
fi

# Detect Pi model
PI_MODEL=""
CPU_INFO=$(cat /proc/cpuinfo | grep "Model" | cut -d: -f2)
if echo "$CPU_INFO" | grep -q "Pi Zero W"; then
    if echo "$CPU_INFO" | grep -q "Rev 1.1"; then
        PI_MODEL="pi_zero_w"
    else
        PI_MODEL="pi_zero_2w"
    fi
elif echo "$CPU_INFO" | grep -q "Pi Zero 2"; then
    PI_MODEL="pi_zero_2w"
elif echo "$CPU_INFO" | grep -q "Pi 3"; then
    PI_MODEL="pi3"
elif echo "$CPU_INFO" | grep -q "Pi 4"; then
    PI_MODEL="pi4"
elif echo "$CPU_INFO" | grep -q "Pi 5"; then
    PI_MODEL="pi5"
else
    # Default to Pi Zero W for unknown models
    PI_MODEL="pi_zero_w"
fi

echo "Detected Pi Model: $PI_MODEL"

# Determine browser based on Pi model
if [ "$PI_MODEL" = "pi_zero_w" ]; then
    BROWSER="surf"
    echo "Browser: surf (lightweight for Pi Zero W)"
else
    BROWSER="chromium-browser"
    echo "Browser: Chromium (full features)"
fi

# Detect config.txt location
CONFIG_FILE=""
OVERLAY_DIR=""
if [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
    OVERLAY_DIR="/boot/overlays"
else
    CONFIG_FILE="/boot/firmware/config.txt"
    OVERLAY_DIR="/boot/firmware/overlays"
fi

echo "Config file: $CONFIG_FILE"
echo ""

# =======================
# STEP 1: System Updates
# =======================
echo "=== STEP 1: Updating System ==="
apt-get update
apt-get upgrade -y
echo -e "${GREEN}✓ System updated${NC}"

# =======================
# STEP 2: Install Dependencies
# =======================
echo ""
echo "=== STEP 2: Installing Dependencies ==="

# Common packages
PACKAGES="git python3-pip python3-venv xserver-xorg xinit x11-xserver-utils matchbox-window-manager unclutter fbset"

# Add browser
if [ "$BROWSER" = "surf" ]; then
    PACKAGES="$PACKAGES surf midori"
else
    PACKAGES="$PACKAGES chromium-browser chromium-browser-l10n"
fi

# Add display-specific packages
if [ "$DISPLAY_TYPE" = "hyperpixel_round" ]; then
    PACKAGES="$PACKAGES python3-smbus python3-spidev python3-numpy python3-pil python3-rpi.gpio i2c-tools raspi-config device-tree-compiler build-essential raspi-gpio"
fi

echo "Installing packages..."
apt-get install -y $PACKAGES
echo -e "${GREEN}✓ Dependencies installed${NC}"

# =======================
# DISPLAY-SPECIFIC SETUP
# =======================

if [ "$DISPLAY_TYPE" = "hyperpixel_round" ]; then
    echo ""
    echo "=== STEP 3: Installing HyperPixel Display ==="
    
    # Critical: Set GL driver to Legacy BEFORE installation
    echo -n "Setting GL driver to Legacy (CRITICAL)... "
    if command -v raspi-config &> /dev/null && raspi-config nonint get_gldriver &>/dev/null; then
        raspi-config nonint do_gldriver G1 2>/dev/null || true
        echo -e "${GREEN}✓${NC}"
    else
        # Disable KMS overlays
        sed -i 's/^dtoverlay=vc4-kms/#dtoverlay=vc4-kms/g' "$CONFIG_FILE"
        sed -i 's/^dtoverlay=vc4-fkms/#dtoverlay=vc4-fkms/g' "$CONFIG_FILE"
        echo -e "${GREEN}✓ (via config)${NC}"
    fi
    
    # Enable I2C and SPI
    echo -n "Enabling I2C and SPI... "
    raspi-config nonint do_i2c 0
    raspi-config nonint do_spi 0
    echo -e "${GREEN}✓${NC}"
    
    # Clone and install HyperPixel driver
    echo "Installing HyperPixel driver..."
    cd /tmp
    rm -rf hyperpixel2r
    git clone https://github.com/pimoroni/hyperpixel2r.git
    cd hyperpixel2r
    bash install.sh
    
    # Create X11 configuration
    mkdir -p /etc/X11/xorg.conf.d
    cat > /etc/X11/xorg.conf.d/99-hyperpixel.conf << 'EOF'
Section "Device"
    Identifier "HyperPixel"
    Driver "fbdev"
    Option "fbdev" "/dev/fb0"
EndSection
EOF
    
    echo -e "${GREEN}✓ HyperPixel installed${NC}"
    REBOOT_REQUIRED=true
    
elif [ "$DISPLAY_TYPE" = "waveshare_34_hdmi" ]; then
    echo ""
    echo "=== STEP 3: Configuring Waveshare Display ==="
    
    # Backup config
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d-%H%M%S)"
    
    # Add Waveshare HDMI configuration
    cat >> "$CONFIG_FILE" << EOF

# Waveshare 3.4inch 800x800 HDMI display
hdmi_group=2
hdmi_mode=87
hdmi_force_hotplug=1
hdmi_timings=800 0 68 32 200 800 0 68 32 200 0 0 0 60 0 59400000 0
disable_overscan=1
EOF
    
    # Enable GPU acceleration for Pi 4/5
    if [ "$PI_MODEL" = "pi4" ] || [ "$PI_MODEL" = "pi5" ]; then
        cat >> "$CONFIG_FILE" << EOF
gpu_mem=128
dtoverlay=vc4-kms-v3d
max_framebuffers=2
EOF
    fi
    
    echo -e "${GREEN}✓ Waveshare configured${NC}"
    REBOOT_REQUIRED=true
fi

# =======================
# STEP 4: Create Display Service
# =======================
echo ""
echo "=== STEP 4: Creating Display Service ==="

# Create start script
mkdir -p /usr/local/bin
cat > /usr/local/bin/start-display.sh << EOF
#!/bin/bash
# Start display for DataOrb

# ============================================
# REMOTE DEBUGGING OPTIONS
# ============================================
# Uncomment the following lines to enable remote debugging:
#
# For Chromium remote debugging (access via chrome://inspect on another computer):
# - Uncomment the REMOTE_DEBUG_PORT line below
# - Add the --remote-debugging-port and --remote-debugging-address flags to chromium-browser
# - Access from your computer: chrome://inspect → Configure → Add pi-ip:9222
#
# REMOTE_DEBUG_PORT=9222
# REMOTE_DEBUG_ADDRESS=0.0.0.0  # Allow connections from any IP (security risk on public networks!)
#
# For SSH X11 forwarding (view display remotely):
# - Connect with: ssh -X pi@raspberry-pi
# - The display will be forwarded to your local machine
#
# For VNC remote desktop:
# - Install VNC: sudo apt-get install realvnc-vnc-server
# - Enable VNC: sudo raspi-config → Interface Options → VNC
# - Connect with VNC Viewer to raspberry-pi:5900
# ============================================

# Kill any existing X sessions
pkill -x Xorg 2>/dev/null || true
pkill -x $BROWSER 2>/dev/null || true
sleep 2

# Enable backlight for HyperPixel
if [ "$DISPLAY_TYPE" = "hyperpixel_round" ]; then
    raspi-gpio set 19 op dh 2>/dev/null || true
fi

# Configure screen timeout (disable by default for kiosk)
xset s off
xset -dpms
xset s noblank

# Start matchbox window manager (no decorations, no cursor)
matchbox-window-manager -use_titlebar no -use_cursor no &
sleep 2

# Start browser in fullscreen
if [ "$BROWSER" = "chromium-browser" ]; then
    # Chromium browser with kiosk mode
    # Uncomment the following lines to enable remote debugging:
    # --remote-debugging-port=\${REMOTE_DEBUG_PORT:-9222} \\
    # --remote-debugging-address=\${REMOTE_DEBUG_ADDRESS:-127.0.0.1} \\
    # --enable-logging --v=1 \\
    exec chromium-browser \\
        --kiosk \\
        --noerrdialogs \\
        --disable-infobars \\
        --no-sandbox \\
        --disable-dev-shm-usage \\
        --disable-gpu \\
        --check-for-update-interval=2592000 \\
        --window-size=\${DISPLAY_WIDTH},\${DISPLAY_HEIGHT} \\
        --window-position=0,0 \\
        http://localhost
else
    # Surf browser (lightweight, no remote debugging available)
    exec surf -F http://localhost
fi
EOF

chmod +x /usr/local/bin/start-display.sh

# Create systemd service
cat > /etc/systemd/system/lcd-display.service << EOF
[Unit]
Description=LCD Display Service
After=multi-user.target network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/root/.Xauthority"
Environment="HOME=/root"
ExecStartPre=/bin/bash -c 'sleep 5'
ExecStart=/usr/bin/xinit /usr/local/bin/start-display.sh -- :0 -nocursor vt2
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable lcd-display.service
echo -e "${GREEN}✓ Display service created${NC}"

# =======================
# STEP 5: Create Test Script
# =======================
echo ""
echo "=== STEP 5: Creating Test Script ==="

cat > /usr/local/bin/test-lcd.sh << 'EOF'
#!/bin/bash
# Test LCD display

# Colors
echo "Testing LCD with color pattern..."

# Kill existing X
pkill -x Xorg 2>/dev/null || true
sleep 2

# Enable backlight if HyperPixel
if grep -q "hyperpixel" /boot/config.txt 2>/dev/null || grep -q "hyperpixel" /boot/firmware/config.txt 2>/dev/null; then
    raspi-gpio set 19 op dh 2>/dev/null || true
fi

# Show test pattern
DISPLAY=:0 xinit /bin/bash -c "
    xsetroot -solid red; sleep 3;
    xsetroot -solid green; sleep 3;
    xsetroot -solid blue; sleep 3;
    xsetroot -solid white; sleep 3;
    xsetroot -solid black
" -- :0 -nocursor vt2

echo "Test complete!"
EOF

chmod +x /usr/local/bin/test-lcd.sh
echo -e "${GREEN}✓ Test script created${NC}"

# =======================
# STEP 6: Final Setup
# =======================
echo ""
echo "=== STEP 6: Final Configuration ==="

# Create a simple test page
mkdir -p /var/www/html
cat > /var/www/html/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(45deg, #1e3c72, #2a5298);
            color: white;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            text-align: center;
        }
        h1 { font-size: 48px; margin: 20px; }
        .info { font-size: 24px; color: #aaa; }
    </style>
</head>
<body>
    <div>
        <h1>LCD Display Working!</h1>
        <div class="info">
            <p id="time"></p>
            <p id="model"></p>
        </div>
    </div>
    <script>
        setInterval(() => {
            document.getElementById('time').textContent = new Date().toLocaleTimeString();
        }, 1000);
        document.getElementById('model').textContent = 'Display: ' + window.innerWidth + 'x' + window.innerHeight;
    </script>
</body>
</html>
EOF

# Install simple web server if not present
if ! command -v nginx &> /dev/null; then
    apt-get install -y nginx
    systemctl enable nginx
    systemctl start nginx
fi

echo -e "${GREEN}✓ Test page created${NC}"

# =======================
# COMPLETION
# =======================
echo ""
echo "========================================="
echo "LCD Installation Complete!"
echo "========================================="
echo ""
echo "Display Type: $DISPLAY_TYPE"
echo "Resolution: ${DISPLAY_WIDTH}x${DISPLAY_HEIGHT}"
echo "Browser: $BROWSER"
echo "Pi Model: $PI_MODEL"
echo ""

if [ "$REBOOT_REQUIRED" = true ]; then
    echo -e "${YELLOW}REBOOT REQUIRED for display to work!${NC}"
    echo ""
    echo "After reboot:"
    echo "1. Test display: sudo test-lcd.sh"
    echo "2. Start service: sudo systemctl start lcd-display"
    echo "3. Check status: sudo systemctl status lcd-display"
    echo ""
    read -p "Reboot now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Rebooting..."
        reboot
    else
        echo "Please reboot manually: sudo reboot"
    fi
else
    echo "You can test the display now:"
    echo "1. Quick test: sudo test-lcd.sh"
    echo "2. Start service: sudo systemctl start lcd-display"
fi

echo "========================================="