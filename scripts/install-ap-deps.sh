#!/bin/bash

# Install dependencies for WiFi Access Point mode
# This script installs hostapd and dnsmasq required for AP functionality

echo "Installing WiFi Access Point dependencies..."

# Update package list
sudo apt-get update

# Install hostapd (for WiFi AP)
echo "Installing hostapd..."
sudo apt-get install -y hostapd

# Install dnsmasq (for DHCP server)
echo "Installing dnsmasq..."
sudo apt-get install -y dnsmasq

# Install wireless tools
echo "Installing wireless tools..."
sudo apt-get install -y wireless-tools

# Stop services (they will be managed by our script)
echo "Stopping default services..."
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
sudo systemctl disable hostapd
sudo systemctl disable dnsmasq

# Enable IP forwarding
echo "Configuring IP forwarding..."
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf

echo "Access Point dependencies installed successfully!"
echo "Services are disabled by default and will be managed by the network-manager script."