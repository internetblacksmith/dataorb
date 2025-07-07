#!/bin/bash

# Dependencies Installation Script for Raspberry Pi

echo "Installing system dependencies for PostHog Display..."

# Update package lists
sudo apt update

# Install required system packages
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    chromium-browser \
    xorg \
    openbox \
    lightdm \
    git \
    curl \
    wget

# Install Node.js 18 (LTS)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Create virtual environment for Python
cd /home/pi/posthog_pi/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install npm dependencies
cd /home/pi/posthog_pi/frontend
npm install

# Configure auto-login for Pi user
sudo raspi-config nonint do_boot_behaviour B4

# Configure X11 to start on boot
sudo systemctl set-default graphical.target
sudo systemctl enable lightdm

echo "Dependencies installation complete!"
echo "Please run the HyperPixel setup script next: ./config/hyperpixel-setup.sh"