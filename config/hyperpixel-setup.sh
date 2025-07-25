#!/bin/bash

# HyperPixel Round Display Setup Script for Pi Zero W
# This script configures the HyperPixel Round display specifically for Raspberry Pi Zero W

echo "🖥️ Setting up HyperPixel Round display for Pi Zero W..."

# Check if we're on Pi Zero W
PI_MODEL=$(cat /proc/cpuinfo | grep "Model" | grep -o "Pi Zero W")
if [ -z "$PI_MODEL" ]; then
    echo "⚠️  Warning: This script is optimized for Pi Zero W"
fi

# Install required packages
sudo apt update
sudo apt install -y git

# Clone official HyperPixel repository for Pi Zero W support
echo "📥 Installing HyperPixel Round drivers..."
cd /tmp
git clone https://github.com/pimoroni/hyperpixel4.git
cd hyperpixel4
sudo ./install.sh --i2c-gpio=7 --spi-gpio

# Configure boot config for HyperPixel Round (Pi Zero W compatible)
echo "⚙️ Configuring display settings for Pi Zero W..."

# Determine correct config file location
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
else
    CONFIG_FILE="/boot/config.txt"
fi

echo "Using config file: $CONFIG_FILE"

# Remove any existing HyperPixel configuration
sudo sed -i '/# HyperPixel/,/^$/d' "$CONFIG_FILE"

# Add Pi Zero W compatible HyperPixel Round configuration
sudo tee -a "$CONFIG_FILE" << 'EOF'

# HyperPixel Round Configuration for Pi Zero W
dtoverlay=vc4-fkms-v3d
display_auto_detect=0
enable_dpi_lcd=1
display_default_lcd=1
dpi_group=2
dpi_mode=87
dpi_output_format=0x7f216
dpi_timings=480 0 10 16 59 480 0 13 3 15 0 0 0 60 0 32000000 8
gpu_mem=128
hdmi_force_hotplug=1
EOF

echo "✅ HyperPixel Round display drivers installed!"
echo
echo "🔄 Please reboot your Raspberry Pi to apply the display changes:"
echo "   sudo reboot"
echo
echo "📝 After reboot:"
echo "1. The round display should be active"
echo "2. Run the PostHog Pi install script if you haven't already"
echo "3. The dashboard should appear on the round display"
echo
echo "🔍 If the display doesn't work after reboot:"
echo "1. Check display connection is secure"
echo "2. Run: sudo dmesg | grep -i -E '(hyperpixel|dpi)'"
echo "3. Check: DISPLAY=:0 xrandr"