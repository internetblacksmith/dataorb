# DataOrb on Raspberry Pi 5 with HDMI Round LCD

## Hardware Setup

### Requirements
- Raspberry Pi 5 (4GB or 8GB recommended)
- HDMI Round LCD Display
- MicroSD Card (32GB+ recommended)
- Power Supply (27W USB-C PD recommended for Pi 5)
- HDMI cable (or micro-HDMI to HDMI adapter)
- Optional: 3D Printed Case - [Download STL files from Cults3D](https://cults3d.com/en/design-collections/printminion/various-cases-for-hyperpixel-2-1-round-touch-display-by-pimoroni)

### Advantages Over Pi Zero W + HyperPixel
- ✅ No GPIO conflicts - WiFi and display work together
- ✅ Much faster performance (10x+ faster)
- ✅ More RAM (8-16x more)
- ✅ HDMI is plug-and-play
- ✅ Latest OS support
- ✅ All connectivity works (WiFi, Bluetooth, Ethernet)

## Software Setup

### 1. OS Installation
```bash
# Use Raspberry Pi Imager
# Select: Raspberry Pi OS (64-bit) - Bookworm
# Enable SSH and WiFi in imager settings
```

### 2. Display Configuration

Edit `/boot/firmware/config.txt`:
```ini
# HDMI Configuration for Round LCD
hdmi_group=2
hdmi_mode=87

# For 480x480 round display (adjust based on your display specs)
hdmi_cvt=480 480 60 1 0 0 0
hdmi_drive=2

# Disable overscan for full screen usage
disable_overscan=1

# GPU memory (Pi 5 can handle more)
gpu_mem=128
```

### 3. Simplified Installation

Since Pi 5 is much more powerful, installation is simpler:

```bash
# Clone repository
git clone https://github.com/jabawack81/pi_analytics_dashboard.git
cd pi_analytics_dashboard

# Install dependencies directly (no memory issues!)
cd frontend
npm install
npm run build
cd ..

# Setup Python environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Run the application
python3 run.py
```

### 4. Kiosk Mode Setup

Create `/home/pi/.config/autostart/dataorb.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=DataOrb Kiosk
Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --enable-features=OverlayScrollbar --start-maximized http://localhost:5000
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

### 5. Performance Optimizations

Not needed! Pi 5 has plenty of power. You can even:
- Run development mode
- Use full Chromium (not Surf)
- Enable animations
- Run multiple services

## Key Differences from Pi Zero W Setup

### What to Remove/Change:
1. **No HyperPixel setup needed** - Remove all hyperpixel2r overlays
2. **No memory limits** - Remove NODE_OPTIONS memory restrictions
3. **No Surf browser** - Use full Chromium
4. **No swap file needed** - Plenty of RAM
5. **Simpler WiFi** - Works out of the box

### What Stays the Same:
1. DataOrb application code
2. Flask backend
3. React frontend
4. API configuration

## Quick Start Script for Pi 5

```bash
#!/bin/bash
# Quick setup for Pi 5

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y git nodejs npm python3-pip python3-venv chromium-browser

# Clone and setup
git clone https://github.com/jabawack81/pi_analytics_dashboard.git
cd pi_analytics_dashboard

# Build frontend (no memory limits needed!)
cd frontend && npm install && npm run build && cd ..

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Configure display for HDMI
echo "Configure your HDMI display in /boot/firmware/config.txt"
echo "Then run: python3 run.py"
```

## WiFi AP Mode

Still works but rarely needed since:
- Ethernet always available
- WiFi more reliable
- Can configure via keyboard/mouse if needed

## Expected Performance

- **Boot time:** ~15-20 seconds (vs 60+ on Pi Zero W)
- **App startup:** ~5 seconds (vs 30+ seconds)
- **Page refresh:** Instant (vs 2-3 seconds)
- **CPU usage:** ~5-10% idle (vs 80-90%)
- **RAM usage:** ~500MB of 4-8GB (vs 400MB of 512MB)

## Troubleshooting

### HDMI Display Not Working?
```bash
# Check HDMI status
tvservice -s

# List supported modes
tvservice -m CEA
tvservice -m DMT

# Force HDMI hotplug
# Add to /boot/firmware/config.txt:
hdmi_force_hotplug=1
```

### Display Resolution Wrong?
```bash
# Use xrandr to check and set resolution
xrandr --output HDMI-1 --mode 480x480
```

## Summary

Pi 5 + HDMI Round LCD = Best combination for DataOrb:
- 🚀 10x better performance
- 🎯 Simpler setup
- 🌐 All connectivity works
- 📺 Better display compatibility
- 💪 No hardware conflicts