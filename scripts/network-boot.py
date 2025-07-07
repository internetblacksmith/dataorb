#!/usr/bin/env python3
"""
Network Boot Script for PostHog Pi
Handles network setup on boot - switches between AP mode and normal mode
"""

import sys
import os
import time
import subprocess
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/posthog-pi-network.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('network-boot')

class NetworkBootManager:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.network_manager_path = self.script_dir / 'network-manager.py'
        self.config_file = self.script_dir.parent / 'backend' / 'device_config.json'
        self.max_connection_attempts = 3
        self.connection_timeout = 30
        
    def log_and_print(self, message, level="info"):
        """Log message and print to console"""
        print(f"[{level.upper()}] {message}")
        getattr(logger, level)(message)
    
    def run_network_command(self, command, timeout=60):
        """Run network manager command"""
        try:
            cmd = ['python3', str(self.network_manager_path), command]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return True, json.loads(result.stdout) if result.stdout else {}
            else:
                return False, {"error": result.stderr}
                
        except subprocess.TimeoutExpired:
            return False, {"error": f"Command '{command}' timed out"}
        except Exception as e:
            return False, {"error": str(e)}
    
    def check_network_connectivity(self):
        """Check if we have internet connectivity"""
        try:
            # Try to ping Google DNS
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '5', '8.8.8.8'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def get_current_mode(self):
        """Get current network mode"""
        success, status = self.run_network_command('status')
        if success:
            if status.get('ap_active', False):
                return 'ap'
            elif status.get('network_connected', False):
                return 'connected'
            else:
                return 'disconnected'
        return 'error'
    
    def attempt_wifi_connection(self):
        """Attempt to connect to configured WiFi"""
        self.log_and_print("Attempting to connect to configured WiFi...")
        
        # Check if we have WiFi config
        if not self.config_file.exists():
            self.log_and_print("No configuration file found", "warning")
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            network_config = config.get('network', {})
            ssid = network_config.get('wifi_ssid')
            password = network_config.get('wifi_password')
            
            if not ssid or not password:
                self.log_and_print("No WiFi credentials configured", "warning")
                return False
            
            self.log_and_print(f"Attempting to connect to SSID: {ssid}")
            
            # Try to connect
            for attempt in range(self.max_connection_attempts):
                self.log_and_print(f"Connection attempt {attempt + 1}/{self.max_connection_attempts}")
                
                try:
                    result = subprocess.run([
                        'python3', str(self.network_manager_path), 'connect', ssid, password
                    ], capture_output=True, text=True, timeout=self.connection_timeout)
                    
                    if result.returncode == 0:
                        connect_result = json.loads(result.stdout)
                        if connect_result.get('success', False):
                            self.log_and_print("WiFi connection successful!")
                            
                            # Wait a bit and verify connectivity
                            time.sleep(10)
                            if self.check_network_connectivity():
                                self.log_and_print("Internet connectivity confirmed")
                                return True
                            else:
                                self.log_and_print("WiFi connected but no internet access", "warning")
                        else:
                            self.log_and_print(f"Connection failed: {connect_result.get('error', 'Unknown error')}", "warning")
                    else:
                        self.log_and_print(f"Connection command failed: {result.stderr}", "warning")
                        
                except subprocess.TimeoutExpired:
                    self.log_and_print(f"Connection attempt {attempt + 1} timed out", "warning")
                except Exception as e:
                    self.log_and_print(f"Connection attempt {attempt + 1} failed: {str(e)}", "warning")
                
                if attempt < self.max_connection_attempts - 1:
                    self.log_and_print("Waiting before next attempt...")
                    time.sleep(5)
            
            self.log_and_print("All connection attempts failed", "error")
            return False
            
        except Exception as e:
            self.log_and_print(f"Error reading configuration: {str(e)}", "error")
            return False
    
    def start_ap_mode(self):
        """Start Access Point mode"""
        self.log_and_print("Starting Access Point mode...")
        
        success, result = self.run_network_command('start-ap', timeout=120)
        
        if success and result.get('success', False):
            self.log_and_print("Access Point mode started successfully")
            self.log_and_print("Setup instructions:")
            self.log_and_print("1. Connect to WiFi network: PostHog-Pi-Setup")
            self.log_and_print("2. Password: posthog123")
            self.log_and_print("3. Open browser: http://192.168.4.1:5000/setup")
            return True
        else:
            self.log_and_print(f"Failed to start AP mode: {result.get('error', 'Unknown error')}", "error")
            return False
    
    def stop_ap_mode(self):
        """Stop Access Point mode"""
        self.log_and_print("Stopping Access Point mode...")
        
        success, result = self.run_network_command('stop-ap')
        
        if success and result.get('success', False):
            self.log_and_print("Access Point mode stopped")
            return True
        else:
            self.log_and_print(f"Failed to stop AP mode: {result.get('error', 'Unknown error')}", "warning")
            return False
    
    def ensure_network_setup(self):
        """Main network setup logic"""
        self.log_and_print("=== PostHog Pi Network Setup ===")
        
        # Check current mode
        current_mode = self.get_current_mode()
        self.log_and_print(f"Current network mode: {current_mode}")
        
        # If already connected, we're done
        if current_mode == 'connected':
            if self.check_network_connectivity():
                self.log_and_print("Already connected to network with internet access")
                return True
            else:
                self.log_and_print("Connected to network but no internet access", "warning")
        
        # If in AP mode, check if we should try to connect
        if current_mode == 'ap':
            self.log_and_print("Currently in AP mode, checking for network configuration...")
            
            # Try to connect to WiFi if configured
            if self.attempt_wifi_connection():
                # Successfully connected, stop AP mode
                self.stop_ap_mode()
                return True
            else:
                self.log_and_print("No WiFi connection available, staying in AP mode")
                return True
        
        # Try to connect to configured WiFi
        if self.attempt_wifi_connection():
            # Stop AP mode if it was running
            if current_mode == 'ap':
                self.stop_ap_mode()
            return True
        
        # No connection available, start AP mode
        self.log_and_print("No network connection available, starting AP mode...")
        return self.start_ap_mode()
    
    def monitor_network(self):
        """Monitor network status and switch modes as needed"""
        self.log_and_print("Starting network monitoring...")
        
        while True:
            try:
                current_mode = self.get_current_mode()
                
                if current_mode == 'connected':
                    # Check if we still have internet
                    if not self.check_network_connectivity():
                        self.log_and_print("Lost internet connectivity, reconfiguring network...")
                        self.ensure_network_setup()
                elif current_mode == 'ap':
                    # Check if we can connect to WiFi now
                    if self.attempt_wifi_connection():
                        self.log_and_print("WiFi connection established, stopping AP mode")
                        self.stop_ap_mode()
                elif current_mode == 'disconnected':
                    # Try to reconnect
                    self.log_and_print("Network disconnected, attempting to reconnect...")
                    self.ensure_network_setup()
                
                # Wait before next check
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                self.log_and_print("Monitoring stopped by user")
                break
            except Exception as e:
                self.log_and_print(f"Error in network monitoring: {str(e)}", "error")
                time.sleep(60)

def main():
    """Main function"""
    manager = NetworkBootManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'setup':
            success = manager.ensure_network_setup()
            sys.exit(0 if success else 1)
        elif command == 'monitor':
            manager.monitor_network()
        elif command == 'status':
            mode = manager.get_current_mode()
            connected = manager.check_network_connectivity()
            print(json.dumps({
                "mode": mode,
                "internet_connected": connected
            }))
        else:
            print("Usage: network-boot.py <setup|monitor|status>")
            sys.exit(1)
    else:
        # Default: ensure network setup
        success = manager.ensure_network_setup()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()