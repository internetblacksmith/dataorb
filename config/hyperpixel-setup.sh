#!/bin/bash

# HyperPixel Round Display Setup Script
# This script configures the HyperPixel Round display for Raspberry Pi

echo "Setting up HyperPixel Round display..."

# Enable SPI
sudo raspi-config nonint do_spi 0

# Install required packages
sudo apt update
sudo apt install -y python3-pip python3-spidev python3-rpi.gpio python3-numpy

# Use the official Pimoroni installer for HyperPixel Round
echo "Installing HyperPixel Round drivers using official installer..."
curl https://get.pimoroni.com/hyperpixel4 | bash

# Configure boot config for HyperPixel Round (480x480 circular)
echo "Configuring display settings..."

# Remove any existing HyperPixel configuration
sudo sed -i '/# HyperPixel/,/^$/d' /boot/config.txt

# Add correct HyperPixel Round configuration
sudo tee -a /boot/config.txt << 'EOF'

# HyperPixel Round Configuration (480x480)
dtoverlay=hyperpixel4:rotate=0
enable_dpi_lcd=1
display_default_lcd=1
dpi_group=2
dpi_mode=87
dpi_output_format=0x7f216
# Timings for 480x480 round display
dpi_timings=480 0 10 16 59 480 0 13 3 15 0 0 0 60 0 32000000 8

# GPU memory split for graphics
gpu_mem=128
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
echo "🔍 If the display doesn't work after reboot, check:"
echo "1. Display connection is secure"
echo "2. Check /boot/config.txt for HyperPixel configuration"
echo "3. Run: sudo dmesg | grep -i hyperpixel"