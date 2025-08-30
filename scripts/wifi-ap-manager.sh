#!/bin/bash
# WiFi Access Point Manager for DataOrb Pi
# Automatically starts AP mode when no network is available

AP_SSID="DataOrb-Setup"
AP_PASS="${DATAORB_AP_PASS:-changeme}"
AP_IP="192.168.4.1"

# Auto-detect WiFi interface to use for AP
# Prefer wlan1 (USB adapter) if available, fallback to wlan0
if ip link show wlan1 >/dev/null 2>&1; then
    AP_INTERFACE="wlan1"
    echo "Using wlan1 (USB WiFi adapter) for Access Point"
else
    AP_INTERFACE="wlan0"
    echo "Using wlan0 (built-in WiFi) for Access Point"
fi

# Function to check if we have network connectivity
check_network() {
    # Check if we can reach a public DNS server or local gateway
    ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1 || \
    ping -c 1 -W 2 1.1.1.1 > /dev/null 2>&1 || \
    ping -c 1 -W 2 $(ip route | grep default | awk '{print $3}' | head -1) > /dev/null 2>&1
}

# Function to check if we have any network interface with IP
check_any_network() {
    # Check if eth0 has an IP (not localhost)
    if ip addr show eth0 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | grep -q "inet "; then
        return 0
    fi
    
    # Check if wireless interface has an IP (not the AP address)
    if ip addr show $AP_INTERFACE 2>/dev/null | grep "inet " | grep -v "inet $AP_IP" | grep -q "inet "; then
        return 0
    fi
    
    return 1
}

# Function to start Access Point
start_ap() {
    echo "📡 Starting WiFi Access Point..."
    
    # Unblock WiFi if it's blocked by rfkill
    if command -v rfkill >/dev/null 2>&1; then
        sudo rfkill unblock wifi 2>/dev/null || true
        sudo rfkill unblock wlan 2>/dev/null || true
    fi
    
    # Check if wireless interface exists
    if ! ip link show $AP_INTERFACE >/dev/null 2>&1; then
        echo "❌ No $AP_INTERFACE interface found. Cannot start AP."
        return 1
    fi
    
    # Install required packages if not present
    if ! command -v hostapd >/dev/null 2>&1; then
        echo "Installing AP software..."
        sudo apt-get update
        sudo apt-get install -y hostapd dnsmasq
    fi
    
    # Stop any existing services
    sudo systemctl stop hostapd 2>/dev/null || true
    sudo systemctl stop dnsmasq 2>/dev/null || true
    sudo systemctl stop wpa_supplicant 2>/dev/null || true
    
    # Kill any wpa_supplicant processes
    sudo killall wpa_supplicant 2>/dev/null || true
    
    # Configure network interface
    sudo ip addr flush dev $AP_INTERFACE
    sudo ip addr add ${AP_IP}/24 dev $AP_INTERFACE
    sudo ip link set $AP_INTERFACE up
    
    # Configure hostapd
    sudo tee /etc/hostapd/hostapd.conf > /dev/null << EOF
interface=$AP_INTERFACE
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
interface=$AP_INTERFACE
dhcp-range=192.168.4.2,192.168.4.100,255.255.255.0,24h
domain=local
address=/dataorb.local/192.168.4.1
EOF
    
    # Start services with error checking
    if ! sudo systemctl start hostapd; then
        echo "❌ Failed to start hostapd"
        sudo journalctl -u hostapd --no-pager -n 20
        return 1
    fi
    
    if ! sudo systemctl start dnsmasq; then
        echo "❌ Failed to start dnsmasq"
        sudo journalctl -u dnsmasq --no-pager -n 20
        sudo systemctl stop hostapd
        return 1
    fi
    
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
    
    # Quick check first
    if [ "$1" = "quick" ]; then
        sleep 2
    else
        # Wait for network to potentially come up
        sleep 10
    fi
    
    # Check if we have ANY network connectivity (eth0 or wlan0)
    if check_network; then
        echo "✅ Network connectivity detected"
        # Make sure AP is stopped if running
        if [ -f /tmp/wifi_ap_mode ]; then
            echo "Stopping AP mode (network available)"
            stop_ap
        fi
    elif check_any_network; then
        echo "⚠️ Have IP but no internet connectivity"
        # Keep current state
    else
        echo "❌ No network connection detected"
        # Start AP mode if not already running
        if [ ! -f /tmp/wifi_ap_mode ]; then
            start_ap
        else
            echo "AP mode already running"
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
    status)
        if [ -f /tmp/wifi_ap_mode ]; then
            echo "✅ Access Point mode is ACTIVE"
            echo "SSID: $AP_SSID"
            echo "IP: $AP_IP"
            sudo systemctl status hostapd --no-pager | head -n 5
            sudo systemctl status dnsmasq --no-pager | head -n 5
        else
            echo "❌ Access Point mode is NOT active"
        fi
        if check_network; then
            echo "✅ Internet connectivity: YES"
        else
            echo "❌ Internet connectivity: NO"
        fi
        ;;
    test)
        echo "Running test mode..."
        echo "Checking rfkill status:"
        if command -v rfkill >/dev/null 2>&1; then
            rfkill list wifi 2>/dev/null || rfkill list 2>/dev/null || echo "rfkill not available"
        else
            echo "rfkill command not found"
        fi
        echo ""
        echo "Checking interfaces:"
        ip link show | grep -E "^[0-9]+: (eth|wlan)"
        echo ""
        echo "Checking network connectivity:"
        if check_network; then
            echo "✅ Have internet"
        else
            echo "❌ No internet"
        fi
        echo ""
        echo "Checking any network:"
        if check_any_network; then
            echo "✅ Have network interface with IP"
        else
            echo "❌ No network interface with IP"
        fi
        ;;
    check|*)
        main "$1"
        ;;
esac