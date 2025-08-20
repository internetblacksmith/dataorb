#!/bin/bash

# Script to automatically fix HyperPixel prerequisites on a fresh Pi
# Run this BEFORE the ansible playbook if test-hyperpixel-install.sh reports errors

set -e

echo "========================================"
echo "HyperPixel Prerequisites Fix Script"
echo "========================================"
echo "This script will fix critical settings required for HyperPixel display"
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

echo "=== APPLYING CRITICAL FIXES ==="

# 1. Most Critical: Set GL Driver to Legacy
echo -n "1. Setting GL driver to Legacy... "
GL_CURRENT=$(raspi-config nonint get_gldriver 2>/dev/null || echo "error")
if [ "$GL_CURRENT" = "1" ]; then
    echo -e "${GREEN}Already set correctly${NC}"
else
    raspi-config nonint do_gldriver G1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Fixed${NC}"
        echo "   Note: Reboot required for this change"
        REBOOT_REQUIRED=true
    else
        echo -e "${RED}✗ Failed${NC}"
    fi
fi

# 2. Enable SPI
echo -n "2. Enabling SPI interface... "
SPI_CURRENT=$(raspi-config nonint get_spi)
if [ "$SPI_CURRENT" = "0" ]; then
    echo -e "${GREEN}Already enabled${NC}"
else
    raspi-config nonint do_spi 0
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Enabled${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
    fi
fi

# 3. Enable I2C
echo -n "3. Enabling I2C interface... "
I2C_CURRENT=$(raspi-config nonint get_i2c)
if [ "$I2C_CURRENT" = "0" ]; then
    echo -e "${GREEN}Already enabled${NC}"
else
    raspi-config nonint do_i2c 0
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Enabled${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
    fi
fi

# 4. Disable conflicting overlays
echo -n "4. Disabling conflicting overlays... "
CONFIG_FILE=""
if [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
elif [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
fi

if [ -n "$CONFIG_FILE" ]; then
    # Backup config
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%s)"
    
    # Comment out conflicting overlays
    sed -i 's/^dtoverlay=vc4-kms/#dtoverlay=vc4-kms/g' "$CONFIG_FILE"
    sed -i 's/^dtoverlay=vc4-fkms/#dtoverlay=vc4-fkms/g' "$CONFIG_FILE"
    sed -i 's/^display_auto_detect=1/#display_auto_detect=1/g' "$CONFIG_FILE"
    
    echo -e "${GREEN}✓ Done${NC}"
else
    echo -e "${RED}✗ Config file not found${NC}"
fi

# 5. Install essential packages
echo -n "5. Installing essential packages... "
apt-get update >/dev/null 2>&1
apt-get install -y git python3-pip python3-rpi.gpio >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Installed${NC}"
else
    echo -e "${YELLOW}⚠ Some packages may have failed${NC}"
fi

echo ""
echo "========================================"
echo "FIXES APPLIED"
echo "========================================"

# Run the test script to verify
echo ""
echo "Running verification test..."
echo ""
bash "$(dirname "$0")/test-hyperpixel-install.sh"

echo ""
if [ "$REBOOT_REQUIRED" = true ]; then
    echo -e "${YELLOW}IMPORTANT: A reboot is required for GL driver changes${NC}"
    echo ""
    read -p "Reboot now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Rebooting..."
        reboot
    else
        echo "Please remember to reboot before running the ansible playbook!"
    fi
fi