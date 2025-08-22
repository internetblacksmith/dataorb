#!/bin/bash

# Simple LCD Enable and Test Script
# Works for both HyperPixel and Waveshare displays
# Just tests if display is working, doesn't install anything

set -e

echo "========================================="
echo "LCD Display Test & Enable Script"
echo "========================================="
echo "This script will test and enable your LCD display"
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

# Detect display type
DISPLAY_TYPE=""
if grep -q "dtoverlay=hyperpixel2r" /boot/config.txt 2>/dev/null || grep -q "dtoverlay=hyperpixel2r" /boot/firmware/config.txt 2>/dev/null; then
    DISPLAY_TYPE="hyperpixel"
    echo "Detected: HyperPixel display"
elif grep -q "hdmi_timings=800" /boot/config.txt 2>/dev/null || grep -q "hdmi_timings=800" /boot/firmware/config.txt 2>/dev/null; then
    DISPLAY_TYPE="waveshare"
    echo "Detected: Waveshare HDMI display"
else
    echo -e "${YELLOW}No display configuration detected${NC}"
    echo "Please run the ansible playbook first"
    exit 1
fi

echo ""
echo "=== Checking Display Components ==="

# Check framebuffer
echo -n "Framebuffer devices: "
if ls /dev/fb* 2>/dev/null; then
    echo -e "${GREEN}✓ Found${NC}"
    fbset -fb /dev/fb0 2>/dev/null || true
else
    echo -e "${RED}✗ Not found${NC}"
    echo "Display may need a reboot to initialize"
fi

# For HyperPixel, check specific services
if [ "$DISPLAY_TYPE" = "hyperpixel" ]; then
    echo -n "HyperPixel init service: "
    if systemctl is-active hyperpixel2r-init >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
    else
        echo -e "${YELLOW}⚠ Not running${NC}"
        systemctl start hyperpixel2r-init 2>/dev/null || true
    fi
    
    # Enable backlight
    echo -n "Backlight control: "
    if raspi-gpio set 19 op dh 2>/dev/null; then
        echo -e "${GREEN}✓ Enabled${NC}"
    else
        echo -e "${YELLOW}⚠ Could not control${NC}"
    fi
fi

# For Waveshare, check HDMI
if [ "$DISPLAY_TYPE" = "waveshare" ]; then
    echo -n "HDMI output: "
    if tvservice -s 2>/dev/null | grep -q "HDMI"; then
        echo -e "${GREEN}✓ Active${NC}"
    else
        echo -e "${YELLOW}⚠ Not detected${NC}"
    fi
fi

# Check X server
echo -n "X server: "
if pgrep Xorg >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${YELLOW}○ Not running${NC}"
fi

# Check display service
echo -n "Display service: "
if systemctl is-active pi-analytics-display >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${YELLOW}○ Not running${NC}"
    echo "  You can start it with: sudo systemctl start pi-analytics-display"
fi

echo ""
echo "=== Quick Display Test ==="
echo "Choose a test:"
echo "1) Show test pattern (colored screens)"
echo "2) Show system info"
echo "3) Start display service"
echo "4) Skip test"
echo ""
read -p "Select (1-4): " -n 1 -r
echo ""

case $REPLY in
    1)
        echo "Showing test pattern (5 seconds each color)..."
        pkill -x Xorg 2>/dev/null || true
        sleep 2
        
        if [ "$DISPLAY_TYPE" = "hyperpixel" ]; then
            raspi-gpio set 19 op dh 2>/dev/null || true
        fi
        
        DISPLAY=:0 xinit /bin/bash -c "
            xsetroot -solid red; sleep 5;
            xsetroot -solid green; sleep 5;
            xsetroot -solid blue; sleep 5;
            xsetroot -solid white; sleep 5
        " -- :0 -nocursor vt2 2>/dev/null
        
        echo -e "${GREEN}✓ Test complete${NC}"
        ;;
        
    2)
        echo "Showing system info on display..."
        pkill -x Xorg 2>/dev/null || true
        sleep 2
        
        if [ "$DISPLAY_TYPE" = "hyperpixel" ]; then
            raspi-gpio set 19 op dh 2>/dev/null || true
        fi
        
        # Create a simple HTML info page
        cat > /tmp/lcd-info.html << EOF
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            background: black;
            color: white;
            font-family: monospace;
            padding: 20px;
            font-size: 24px;
        }
        h1 { color: lime; }
        .info { color: cyan; }
    </style>
</head>
<body>
    <h1>LCD Display Working!</h1>
    <div class="info">
        <p>Display: $DISPLAY_TYPE</p>
        <p>Model: $(cat /proc/device-tree/model 2>/dev/null | tr -d '\0')</p>
        <p>IP: $(hostname -I | cut -d' ' -f1)</p>
        <p>Time: $(date)</p>
    </div>
</body>
</html>
EOF
        
        DISPLAY=:0 xinit /bin/bash -c "
            matchbox-window-manager -use_titlebar no -use_cursor no &
            sleep 2;
            surf -F file:///tmp/lcd-info.html
        " -- :0 -nocursor vt2 2>/dev/null &
        
        echo -e "${GREEN}✓ Info displayed${NC}"
        echo "Press Ctrl+C to stop"
        ;;
        
    3)
        echo "Starting display service..."
        systemctl start pi-analytics-display
        sleep 3
        if systemctl is-active pi-analytics-display >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Service started${NC}"
        else
            echo -e "${RED}✗ Service failed to start${NC}"
            echo "Check logs: journalctl -u pi-analytics-display -n 50"
        fi
        ;;
        
    4)
        echo "Skipping test"
        ;;
        
    *)
        echo "Invalid option"
        ;;
esac

echo ""
echo "========================================="
echo "LCD Test Complete"
echo "========================================="

if [ "$DISPLAY_TYPE" = "hyperpixel" ]; then
    echo "If display is black, check:"
    echo "1. GL driver: raspi-config nonint get_gldriver (should be 1)"
    echo "2. Reboot if just installed"
    echo "3. Backlight: sudo raspi-gpio set 19 op dh"
fi

if [ "$DISPLAY_TYPE" = "waveshare" ]; then
    echo "If display is black, check:"
    echo "1. HDMI cable connection"
    echo "2. Power to both Pi and LCD"
    echo "3. Boot config: grep hdmi /boot/config.txt"
fi

echo ""
echo "Useful commands:"
echo "- Start service: sudo systemctl start pi-analytics-display"
echo "- Check status: sudo systemctl status pi-analytics-display"
echo "- View logs: journalctl -u pi-analytics-display -f"
echo "========================================="