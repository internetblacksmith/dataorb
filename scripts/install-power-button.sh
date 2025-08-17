#!/bin/bash
#
# Install script for DataOrb power button monitor
# Sets up the power button monitoring service with I2C/GPIO support
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "DataOrb Power Button Monitor Installation"
echo "=========================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Install required Python packages
echo "Installing Python dependencies..."
pip3 install smbus RPi.GPIO || true

# Enable alternate I2C bus for HyperPixel
echo "Configuring alternate I2C bus..."
if ! grep -q "dtoverlay=i2c-gpio,bus=3" /boot/config.txt; then
    cat >> /boot/config.txt << EOF

# Alternate I2C bus for HyperPixel (BCM10/11)
dtparam=i2c_vc=on
dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=10,i2c_gpio_scl=11
EOF
    echo "Added I2C bus 3 configuration to /boot/config.txt"
else
    echo "I2C bus 3 already configured"
fi

# Make power button script executable
chmod +x "$PROJECT_DIR/scripts/power_button_monitor.py"

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/dataorb-power-button.service << EOF
[Unit]
Description=DataOrb Power Button Monitor
After=multi-user.target
Before=dataorb-display.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 $PROJECT_DIR/scripts/power_button_monitor.py
Restart=always
RestartSec=5
User=root
StandardOutput=journal
StandardError=journal

# Environment
Environment="PYTHONUNBUFFERED=1"

# Restart conditions
RestartPreventExitStatus=0
SuccessExitStatus=0

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "Enabling power button service..."
systemctl daemon-reload
systemctl enable dataorb-power-button.service

# Check for I2C devices
echo ""
echo "Checking for I2C devices..."
if command -v i2cdetect &> /dev/null; then
    echo "I2C Bus 1 (standard):"
    i2cdetect -y 1 2>/dev/null || echo "Bus 1 not available"
    echo ""
    echo "I2C Bus 3 (HyperPixel alternate):"
    i2cdetect -y 3 2>/dev/null || echo "Bus 3 not available (will be available after reboot)"
else
    echo "i2cdetect not found. Install with: apt-get install i2c-tools"
fi

# Provide instructions
echo ""
echo "Installation complete!"
echo ""
echo "Hardware Setup Instructions:"
echo "============================"
echo ""
echo "Option 1: Using MCP23017 (Recommended)"
echo "--------------------------------------"
echo "1. Connect MCP23017 to HyperPixel I2C breakout:"
echo "   - VDD → 3.3V"
echo "   - VSS → GND"
echo "   - SCL → BCM11 (I2C-3 SCL)"
echo "   - SDA → BCM10 (I2C-3 SDA)"
echo "   - A0, A1, A2 → GND (for address 0x20)"
echo ""
echo "2. Connect button:"
echo "   - Button → MCP23017 GPA0 (pin 21) and GND"
echo ""
echo "3. Optional LED:"
echo "   - LED + resistor → MCP23017 GPA1 (pin 22) and GND"
echo ""
echo "Option 2: Using RUN Header Only"
echo "-------------------------------"
echo "1. Solder 2-pin header to RUN pads on Pi Zero"
echo "2. Connect momentary button between RUN pins"
echo "3. This provides wake from halt only"
echo ""
echo "Next Steps:"
echo "-----------"
echo "1. Reboot to activate I2C bus 3: sudo reboot"
echo "2. After reboot, verify I2C device: i2cdetect -y 3"
echo "3. Start the service: sudo systemctl start dataorb-power-button"
echo "4. Check status: sudo systemctl status dataorb-power-button"
echo "5. View logs: journalctl -u dataorb-power-button -f"
echo ""
echo "Testing:"
echo "--------"
echo "- Press and hold button for 3 seconds to shutdown"
echo "- After shutdown, press button on RUN header to wake"
echo ""