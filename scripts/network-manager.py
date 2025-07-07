#!/usr/bin/env python3
"""
Network Manager for PostHog Pi
Handles network detection, WiFi AP setup, and network transitions
"""

import subprocess
import json
import time
import os
import sys
from typing import Dict, List, Optional, Tuple

class NetworkManager:
    def __init__(self, config_file: str = "/home/paolo/dev/posthog_pi/backend/device_config.json"):
        self.config_file = config_file
        self.ap_interface = "wlan0"
        self.ap_ssid = "PostHog-Pi-Setup"
        self.ap_password = "posthog123"
        self.ap_ip = "192.168.4.1"
        self.ap_range = "192.168.4.2,192.168.4.20"
        
    def run_command(self, command: str, check: bool = True) -> Tuple[int, str, str]:
        """Execute shell command and return (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timeout"
        except Exception as e:
            return 1, "", str(e)
    
    def check_network_connection(self) -> bool:
        """Check if device has internet connectivity"""
        # Try to ping common DNS servers
        dns_servers = ["8.8.8.8", "1.1.1.1", "8.8.4.4"]
        
        for dns in dns_servers:
            retcode, _, _ = self.run_command(f"ping -c 1 -W 3 {dns}")
            if retcode == 0:
                return True
        return False
    
    def get_wifi_status(self) -> Dict[str, str]:
        """Get current WiFi connection status"""
        retcode, stdout, stderr = self.run_command("iwconfig wlan0 2>/dev/null")
        
        if retcode != 0:
            return {"status": "interface_error", "ssid": "", "signal": ""}
        
        lines = stdout.split('\n')
        status = {"status": "disconnected", "ssid": "", "signal": ""}
        
        for line in lines:
            if "ESSID:" in line:
                essid_part = line.split("ESSID:")[1].strip()
                if essid_part != 'off/any' and essid_part != '""':
                    status["ssid"] = essid_part.strip('"')
                    status["status"] = "connected"
            elif "Signal level=" in line:
                signal_part = line.split("Signal level=")[1].split()[0]
                status["signal"] = signal_part
        
        return status
    
    def scan_networks(self) -> List[Dict[str, str]]:
        """Scan for available WiFi networks"""
        retcode, stdout, stderr = self.run_command("iwlist wlan0 scan 2>/dev/null")
        
        if retcode != 0:
            return []
        
        networks = []
        current_network = {}
        
        for line in stdout.split('\n'):
            line = line.strip()
            if line.startswith("Cell"):
                if current_network:
                    networks.append(current_network)
                current_network = {}
            elif "ESSID:" in line:
                essid = line.split("ESSID:")[1].strip().strip('"')
                if essid:
                    current_network["ssid"] = essid
            elif "Quality=" in line:
                quality_part = line.split("Quality=")[1].split()[0]
                current_network["quality"] = quality_part
            elif "Encryption key:" in line:
                encryption = "on" if "on" in line else "off"
                current_network["encryption"] = encryption
        
        if current_network:
            networks.append(current_network)
        
        return networks
    
    def load_wifi_config(self) -> Optional[Dict[str, str]]:
        """Load WiFi configuration from device config"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    network_config = config.get("network", {})
                    if network_config.get("wifi_ssid") and network_config.get("wifi_password"):
                        return {
                            "ssid": network_config["wifi_ssid"],
                            "password": network_config["wifi_password"]
                        }
        except Exception as e:
            print(f"Error loading WiFi config: {e}")
        
        return None
    
    def connect_to_wifi(self, ssid: str, password: str) -> bool:
        """Connect to WiFi network"""
        # Create wpa_supplicant config
        wpa_config = f"""
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""
        
        try:
            # Write temporary config
            with open("/tmp/wpa_supplicant.conf", "w") as f:
                f.write(wpa_config)
            
            # Stop any existing wpa_supplicant
            self.run_command("sudo killall wpa_supplicant 2>/dev/null", check=False)
            time.sleep(2)
            
            # Start wpa_supplicant
            retcode, _, _ = self.run_command(
                f"sudo wpa_supplicant -B -i {self.ap_interface} -c /tmp/wpa_supplicant.conf"
            )
            
            if retcode != 0:
                return False
            
            # Request DHCP
            time.sleep(5)
            retcode, _, _ = self.run_command(f"sudo dhclient {self.ap_interface}")
            
            # Wait and check connection
            time.sleep(10)
            return self.check_network_connection()
            
        except Exception as e:
            print(f"Error connecting to WiFi: {e}")
            return False
    
    def is_ap_mode_active(self) -> bool:
        """Check if AP mode is currently active"""
        retcode, stdout, _ = self.run_command("ps aux | grep hostapd | grep -v grep")
        return retcode == 0 and "hostapd" in stdout
    
    def start_ap_mode(self) -> bool:
        """Start WiFi Access Point mode"""
        try:
            # Stop any existing network services
            self.run_command("sudo systemctl stop dhcpcd", check=False)
            self.run_command("sudo systemctl stop wpa_supplicant", check=False)
            self.run_command("sudo killall hostapd 2>/dev/null", check=False)
            self.run_command("sudo killall dnsmasq 2>/dev/null", check=False)
            
            # Configure interface
            retcode, _, _ = self.run_command(f"sudo ip link set {self.ap_interface} down")
            if retcode != 0:
                return False
            
            retcode, _, _ = self.run_command(f"sudo ip addr flush dev {self.ap_interface}")
            if retcode != 0:
                return False
            
            retcode, _, _ = self.run_command(f"sudo ip addr add {self.ap_ip}/24 dev {self.ap_interface}")
            if retcode != 0:
                return False
            
            retcode, _, _ = self.run_command(f"sudo ip link set {self.ap_interface} up")
            if retcode != 0:
                return False
            
            # Create hostapd config
            hostapd_config = f"""
interface={self.ap_interface}
driver=nl80211
ssid={self.ap_ssid}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={self.ap_password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
            
            with open("/tmp/hostapd.conf", "w") as f:
                f.write(hostapd_config)
            
            # Create dnsmasq config
            dnsmasq_config = f"""
interface={self.ap_interface}
dhcp-range={self.ap_range},255.255.255.0,24h
"""
            
            with open("/tmp/dnsmasq.conf", "w") as f:
                f.write(dnsmasq_config)
            
            # Start hostapd
            retcode, _, stderr = self.run_command(
                "sudo hostapd /tmp/hostapd.conf -B"
            )
            
            if retcode != 0:
                print(f"Failed to start hostapd: {stderr}")
                return False
            
            # Start dnsmasq
            retcode, _, stderr = self.run_command(
                "sudo dnsmasq -C /tmp/dnsmasq.conf"
            )
            
            if retcode != 0:
                print(f"Failed to start dnsmasq: {stderr}")
                return False
            
            # Enable IP forwarding
            self.run_command("sudo sysctl net.ipv4.ip_forward=1", check=False)
            
            print(f"AP mode started: {self.ap_ssid}")
            print(f"Connect to WiFi: {self.ap_ssid}")
            print(f"Password: {self.ap_password}")
            print(f"Setup URL: http://{self.ap_ip}:5000/config")
            
            return True
            
        except Exception as e:
            print(f"Error starting AP mode: {e}")
            return False
    
    def stop_ap_mode(self) -> bool:
        """Stop WiFi Access Point mode"""
        try:
            # Stop services
            self.run_command("sudo killall hostapd 2>/dev/null", check=False)
            self.run_command("sudo killall dnsmasq 2>/dev/null", check=False)
            
            # Reset interface
            self.run_command(f"sudo ip addr flush dev {self.ap_interface}", check=False)
            self.run_command(f"sudo ip link set {self.ap_interface} down", check=False)
            
            # Clean up config files
            self.run_command("sudo rm -f /tmp/hostapd.conf /tmp/dnsmasq.conf", check=False)
            
            print("AP mode stopped")
            return True
            
        except Exception as e:
            print(f"Error stopping AP mode: {e}")
            return False
    
    def determine_network_mode(self) -> str:
        """Determine what network mode the device should be in"""
        # Check if already in AP mode
        if self.is_ap_mode_active():
            return "ap"
        
        # Check if we have network connectivity
        if self.check_network_connection():
            return "connected"
        
        # Check if we have WiFi config
        wifi_config = self.load_wifi_config()
        if wifi_config:
            # Try to connect to configured network
            if self.connect_to_wifi(wifi_config["ssid"], wifi_config["password"]):
                return "connected"
        
        # No connectivity, start AP mode
        return "needs_ap"
    
    def ensure_network_setup(self) -> str:
        """Ensure proper network setup, return current mode"""
        mode = self.determine_network_mode()
        
        if mode == "needs_ap":
            if self.start_ap_mode():
                return "ap"
            else:
                return "error"
        
        return mode

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: network-manager.py <command>")
        print("Commands: status, scan, connect, start-ap, stop-ap, ensure-setup")
        return
    
    command = sys.argv[1]
    nm = NetworkManager()
    
    if command == "status":
        wifi_status = nm.get_wifi_status()
        network_connected = nm.check_network_connection()
        ap_active = nm.is_ap_mode_active()
        
        print(json.dumps({
            "wifi_status": wifi_status,
            "network_connected": network_connected,
            "ap_active": ap_active
        }, indent=2))
    
    elif command == "scan":
        networks = nm.scan_networks()
        print(json.dumps(networks, indent=2))
    
    elif command == "connect":
        if len(sys.argv) < 4:
            print("Usage: network-manager.py connect <ssid> <password>")
            return
        
        ssid = sys.argv[2]
        password = sys.argv[3]
        success = nm.connect_to_wifi(ssid, password)
        print(json.dumps({"success": success}))
    
    elif command == "start-ap":
        success = nm.start_ap_mode()
        print(json.dumps({"success": success}))
    
    elif command == "stop-ap":
        success = nm.stop_ap_mode()
        print(json.dumps({"success": success}))
    
    elif command == "ensure-setup":
        mode = nm.ensure_network_setup()
        print(json.dumps({"mode": mode}))
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()