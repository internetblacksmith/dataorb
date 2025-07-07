#!/bin/bash

# HyperPixel Round Display Setup Script
# This script configures the HyperPixel Round display for Raspberry Pi

echo "Setting up HyperPixel Round display..."

# Enable SPI
sudo raspi-config nonint do_spi 0

# Install required packages
sudo apt update
sudo apt install -y python3-pip python3-spidev python3-rpi.gpio python3-numpy

# Download and install HyperPixel drivers
cd /tmp
wget https://github.com/pimoroni/hyperpixel4/releases/latest/download/hyperpixel4-install.sh
chmod +x hyperpixel4-install.sh
sudo ./hyperpixel4-install.sh

# Configure boot config for HyperPixel Round
sudo tee -a /boot/config.txt << 'EOF'

# HyperPixel Round Configuration
dtoverlay=hyperpixel4
enable_dpi_lcd=1
display_default_lcd=1
dpi_group=2
dpi_mode=87
dpi_output_format=0x7f216
dpi_timings=480 0 10 16 59 480 0 13 3 15 0 0 0 60 0 32000000 8

# Rotate display for round orientation
display_rotate=1

# GPU memory split
gpu_mem=64
EOF

# Set up autostart for kiosk mode
sudo mkdir -p /etc/systemd/system
sudo tee /etc/systemd/system/posthog-display.service << 'EOF'
[Unit]
Description=PostHog Display Dashboard
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/posthog_pi
ExecStart=/home/pi/posthog_pi/scripts/start-kiosk.sh
Restart=always
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable posthog-display.service

echo "HyperPixel Round display setup complete!"
echo "Please reboot your Raspberry Pi to apply the changes."
echo "After reboot, the display should be configured correctly."