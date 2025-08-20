#!/bin/bash

# Standalone HyperPixel 2.1 Round LCD Installation and Test Script
# This script incorporates ALL lessons learned from our troubleshooting
# Run on a FRESH Raspberry Pi OS installation (Bullseye recommended)

set -e

echo "========================================="
echo "HyperPixel 2.1 Round LCD Complete Setup"
echo "========================================="
echo "This script will install and test the HyperPixel display"
echo "Based on all troubleshooting lessons learned"
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

echo "Using config: $CONFIG_FILE"
echo "Using overlays: $OVERLAY_DIR"
echo ""

# =======================
# STEP 1: Prerequisites
# =======================
echo "=== STEP 1: Installing Prerequisites ==="

echo "Updating package list..."
apt-get update

echo "Installing required packages..."
apt-get install -y \
    git \
    python3-pip \
    python3-smbus \
    python3-spidev \
    python3-numpy \
    python3-pil \
    python3-rpi.gpio \
    i2c-tools \
    raspi-config \
    device-tree-compiler \
    build-essential \
    xserver-xorg \
    xinit \
    x11-xserver-utils \
    matchbox-window-manager \
    surf \
    fbset

echo -e "${GREEN}✓ Prerequisites installed${NC}"

# =======================
# STEP 2: Critical Settings
# =======================
echo ""
echo "=== STEP 2: Configuring Critical Settings ==="

# MOST CRITICAL: Set GL driver to Legacy (if supported)
echo -n "Setting GL driver to Legacy (CRITICAL)... "
if command -v raspi-config &> /dev/null && raspi-config nonint get_gldriver &>/dev/null; then
    GL_CURRENT=$(raspi-config nonint get_gldriver 2>/dev/null || echo "error")
    if [ "$GL_CURRENT" != "1" ]; then
        raspi-config nonint do_gldriver G1 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Set to Legacy${NC}"
            REBOOT_REQUIRED=true
        else
            echo -e "${YELLOW}⚠ Could not set (may be using older Pi OS)${NC}"
        fi
    else
        echo -e "${GREEN}✓ Already Legacy${NC}"
    fi
else
    echo -e "${YELLOW}⚠ GL driver control not available${NC}"
    echo "  Ensuring no KMS overlays are enabled instead..."
    # Make sure KMS is disabled in config
    sed -i 's/^dtoverlay=vc4-kms/#dtoverlay=vc4-kms/g' "$CONFIG_FILE" 2>/dev/null
    sed -i 's/^dtoverlay=vc4-fkms/#dtoverlay=vc4-fkms/g' "$CONFIG_FILE" 2>/dev/null
fi

# Enable I2C
echo -n "Enabling I2C... "
raspi-config nonint do_i2c 0
echo -e "${GREEN}✓${NC}"

# Enable SPI
echo -n "Enabling SPI... "
raspi-config nonint do_spi 0
echo -e "${GREEN}✓${NC}"

# =======================
# STEP 3: Clean Conflicts
# =======================
echo ""
echo "=== STEP 3: Removing Conflicting Settings ==="

# Backup config
cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d-%H%M%S)"

# Remove conflicting overlays
echo "Disabling conflicting overlays..."
sed -i 's/^dtoverlay=vc4-kms/#dtoverlay=vc4-kms # Disabled for HyperPixel/g' "$CONFIG_FILE"
sed -i 's/^dtoverlay=vc4-fkms/#dtoverlay=vc4-fkms # Disabled for HyperPixel/g' "$CONFIG_FILE"
sed -i 's/^dtoverlay=vc4-kms-dpi-hyperpixel2r/#dtoverlay=vc4-kms-dpi-hyperpixel2r # Not compatible/g' "$CONFIG_FILE"
sed -i 's/^display_auto_detect=1/#display_auto_detect=1 # Disabled for HyperPixel/g' "$CONFIG_FILE"

# Remove any existing hyperpixel config to start fresh
sed -i '/# BEGIN HYPERPIXEL CONFIG/,/# END HYPERPIXEL CONFIG/d' "$CONFIG_FILE"

echo -e "${GREEN}✓ Conflicts removed${NC}"

# =======================
# STEP 4: Install HyperPixel
# =======================
echo ""
echo "=== STEP 4: Installing HyperPixel Driver ==="

# Clone official repository
echo "Cloning official HyperPixel repository..."
cd /tmp
rm -rf hyperpixel2r
git clone https://github.com/pimoroni/hyperpixel2r.git
cd hyperpixel2r

# Run official installer
echo "Running official installer..."
bash install.sh

# Verify installation
echo ""
echo "Verifying installation..."
if [ -f "$OVERLAY_DIR/hyperpixel2r.dtbo" ]; then
    echo -e "${GREEN}✓ Device tree overlay installed${NC}"
else
    echo -e "${RED}✗ Overlay not found!${NC}"
fi

if [ -f "/usr/bin/hyperpixel2r-init" ]; then
    echo -e "${GREEN}✓ Init binary installed${NC}"
else
    echo -e "${RED}✗ Init binary not found!${NC}"
fi

if systemctl list-unit-files | grep -q hyperpixel2r-init; then
    echo -e "${GREEN}✓ Systemd service installed${NC}"
    systemctl enable hyperpixel2r-init
else
    echo -e "${RED}✗ Service not found!${NC}"
fi

# =======================
# STEP 5: X11 Configuration
# =======================
echo ""
echo "=== STEP 5: Configuring X11 for HyperPixel ==="

# Create X11 config directory
mkdir -p /etc/X11/xorg.conf.d

# Force X to use fb0 (HyperPixel)
cat > /etc/X11/xorg.conf.d/99-hyperpixel.conf << 'EOF'
Section "Device"
    Identifier "HyperPixel"
    Driver "fbdev"
    Option "fbdev" "/dev/fb0"
EndSection

Section "Screen"
    Identifier "HyperPixelScreen"
    Device "HyperPixel"
    DefaultDepth 24
EndSection

Section "ServerLayout"
    Identifier "HyperPixelLayout"
    Screen "HyperPixelScreen"
EndSection
EOF

echo -e "${GREEN}✓ X11 configured for fb0${NC}"

# =======================
# STEP 6: Test Script
# =======================
echo ""
echo "=== STEP 6: Creating Test Script ==="

# Create a simple test script
cat > /usr/local/bin/test-hyperpixel.sh << 'EOF'
#!/bin/bash
# Kill any existing X sessions
pkill -x Xorg 2>/dev/null
pkill -x xinit 2>/dev/null
sleep 2

# Turn on backlight
raspi-gpio set 19 op dh 2>/dev/null || true

# Start X with a simple test
echo "Starting X server with test pattern..."
xinit /bin/bash -c "matchbox-window-manager & xsetroot -solid red; sleep 5; xsetroot -solid green; sleep 5; xsetroot -solid blue; sleep 5" -- :0 -nocursor
EOF

chmod +x /usr/local/bin/test-hyperpixel.sh

echo -e "${GREEN}✓ Test script created${NC}"

# =======================
# STEP 7: Create Display Service
# =======================
echo ""
echo "=== STEP 7: Creating Display Service ==="

cat > /etc/systemd/system/hyperpixel-test.service << 'EOF'
[Unit]
Description=HyperPixel Test Display
After=multi-user.target hyperpixel2r-init.service
Wants=hyperpixel2r-init.service

[Service]
Type=simple
User=root
Environment="DISPLAY=:0"
ExecStartPre=/bin/bash -c 'sleep 5; pkill -x Xorg || true'
ExecStart=/usr/bin/xinit /bin/bash -c "matchbox-window-manager -use_titlebar no -use_cursor no & surf -F https://www.raspberrypi.org" -- :0 -nocursor vt2
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo -e "${GREEN}✓ Service created${NC}"

# =======================
# STEP 8: Final Checks
# =======================
echo ""
echo "=== STEP 8: Final System Checks ==="

# Check GL driver (may not be available on all systems)
if command -v raspi-config &> /dev/null; then
    GL_CHECK=$(raspi-config nonint get_gldriver 2>/dev/null || echo "unknown")
    if [ "$GL_CHECK" = "1" ]; then
        echo -e "${GREEN}✓ GL Driver: Legacy (correct)${NC}"
    elif [ "$GL_CHECK" = "unknown" ]; then
        echo -e "${YELLOW}⚠ GL Driver: Unable to check (older raspi-config)${NC}"
        # Alternative check for KMS in config
        if grep -q "^dtoverlay=vc4-kms" "$CONFIG_FILE" || grep -q "^dtoverlay=vc4-fkms" "$CONFIG_FILE"; then
            echo -e "${RED}  KMS overlay detected - may cause issues${NC}"
        else
            echo -e "${GREEN}  No KMS overlays found (good)${NC}"
        fi
    else
        echo -e "${RED}✗ GL Driver: NOT Legacy (will cause black screen!)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ raspi-config not found${NC}"
fi

# Check for framebuffers
if [ -e /dev/fb0 ]; then
    FB0_SIZE=$(cat /sys/class/graphics/fb0/virtual_size 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓ Framebuffer fb0: $FB0_SIZE${NC}"
else
    echo -e "${YELLOW}⚠ fb0 not found (will appear after reboot)${NC}"
fi

# Check SPI devices
if ls /dev/spi* 2>/dev/null; then
    echo -e "${GREEN}✓ SPI devices found${NC}"
else
    echo -e "${YELLOW}⚠ SPI devices not found (will appear after reboot)${NC}"
fi

# Check boot config
if grep -q "dtoverlay=hyperpixel2r" "$CONFIG_FILE"; then
    echo -e "${GREEN}✓ HyperPixel overlay configured${NC}"
else
    echo -e "${RED}✗ HyperPixel overlay NOT in config!${NC}"
fi

# =======================
# STEP 9: Quick Test
# =======================
echo ""
echo "========================================="
echo "INSTALLATION COMPLETE"
echo "========================================="
echo ""

# Check if this is first run after HyperPixel installation
if [ -f "$OVERLAY_DIR/hyperpixel2r.dtbo" ] && [ ! -e /dev/fb0 ]; then
    echo -e "${YELLOW}IMPORTANT: Reboot required for HyperPixel driver to initialize${NC}"
    echo "The display driver needs a reboot to create framebuffer devices."
    REBOOT_REQUIRED=true
fi

if [ "$REBOOT_REQUIRED" = true ]; then
    echo -e "${YELLOW}REBOOT REQUIRED for changes to take effect${NC}"
    echo ""
    echo "After reboot, test the display with:"
    echo "  sudo /usr/local/bin/test-hyperpixel.sh"
    echo ""
    echo "Or enable the test service:"
    echo "  sudo systemctl enable --now hyperpixel-test"
    echo ""
    read -p "Reboot now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Rebooting..."
        reboot
    else
        echo -e "${RED}Please reboot manually before testing the display${NC}"
        echo "The display will NOT work until after reboot!"
    fi
else
    echo -e "${YELLOW}Note: If HyperPixel was just installed, a reboot is required${NC}"
    echo ""
    echo "You can try testing now, but if it fails, reboot first:"
    echo "  sudo /usr/local/bin/test-hyperpixel.sh"
    echo ""
    echo "This will show red, green, blue screens for 5 seconds each"
    echo ""
    read -p "Run test now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Check if framebuffer exists
        if [ ! -e /dev/fb0 ]; then
            echo -e "${RED}No framebuffer found - reboot required first!${NC}"
            echo "Run: sudo reboot"
            exit 1
        fi
        # Turn on backlight first
        raspi-gpio set 19 op dh 2>/dev/null || true
        /usr/local/bin/test-hyperpixel.sh
    fi
fi

echo ""
echo "========================================="
echo "If the display doesn't work, check:"
echo "1. GL driver: raspi-config nonint get_gldriver (must be 1)"
echo "2. Framebuffer: ls -la /dev/fb*"
echo "3. Service: systemctl status hyperpixel2r-init"
echo "4. Backlight: sudo raspi-gpio set 19 op dh"
echo "========================================="