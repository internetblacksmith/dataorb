#!/bin/bash
# WiFi Access Point Manager for PostHog Pi
# Automatically starts AP mode when no network is available

set -e

AP_SSID="PostHog-Setup"
AP_PASS="posthog123"
AP_IP="192.168.4.1"

# Function to check network connectivity
check_network() {
    # Check if we have an IP address on wlan0 (not the AP address)
    ip addr show wlan0 | grep -q "inet " && \
    ! ip addr show wlan0 | grep -q "inet $AP_IP"
}

# Function to check if connected to WiFi
check_wifi_connected() {
    iwgetid -r > /dev/null 2>&1
}

# Function to start Access Point
start_ap() {
    echo "📡 Starting WiFi Access Point..."
    
    # Install required packages if not present
    if ! command -v hostapd >/dev/null 2>&1; then
        echo "Installing AP software..."
        sudo apt-get update
        sudo apt-get install -y hostapd dnsmasq
    fi
    
    # Stop any existing services
    sudo systemctl stop hostapd 2>/dev/null || true
    sudo systemctl stop dnsmasq 2>/dev/null || true
    
    # Configure network interface
    sudo ip addr flush dev wlan0
    sudo ip addr add ${AP_IP}/24 dev wlan0
    sudo ip link set wlan0 up
    
    # Configure hostapd
    sudo tee /etc/hostapd/hostapd.conf > /dev/null << EOF
interface=wlan0
driver=nl80211
ssid=$AP_SSID
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$AP_PASS
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF
    
    # Configure dnsmasq
    sudo tee /etc/dnsmasq.conf > /dev/null << EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.100,255.255.255.0,24h
domain=local
address=/posthog.local/192.168.4.1
EOF
    
    # Start services
    sudo systemctl start hostapd
    sudo systemctl start dnsmasq
    
    # Enable IP forwarding
    sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null
    
    # Create marker file
    touch /tmp/wifi_ap_mode
    
    echo "✅ Access Point started: $AP_SSID"
}

# Function to stop Access Point
stop_ap() {
    echo "📡 Stopping Access Point..."
    
    sudo systemctl stop hostapd 2>/dev/null || true
    sudo systemctl stop dnsmasq 2>/dev/null || true
    
    # Remove marker file
    rm -f /tmp/wifi_ap_mode
    
    # Restart networking
    sudo systemctl restart networking
    sudo systemctl restart wpa_supplicant
}

# Main logic
main() {
    echo "🔍 Checking network connectivity..."
    
    # Wait a bit for network to come up
    sleep 10
    
    # Check if we have network connectivity
    if check_wifi_connected; then
        echo "✅ WiFi connected"
        # Make sure AP is stopped if running
        if [ -f /tmp/wifi_ap_mode ]; then
            stop_ap
        fi
    else
        echo "❌ No WiFi connection detected"
        # Start AP mode if not already running
        if [ ! -f /tmp/wifi_ap_mode ]; then
            start_ap
        fi
    fi
}

# Run based on argument
case "${1:-check}" in
    start)
        start_ap
        ;;
    stop)
        stop_ap
        ;;
    check|*)
        main
        ;;
esac