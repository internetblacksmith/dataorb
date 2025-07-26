# PostHog Pi - Quick Start Guide

## 🚀 Easy Installation on Fresh Raspberry Pi

### **One-Command Installation**

After flashing Raspberry Pi OS and first boot:

```bash
curl -sSL https://raw.githubusercontent.com/jabawack81/pi_analytics_dashboard/main/scripts/install-pi.sh | bash
```

Or manually:

```bash
# Download and run installer
wget https://raw.githubusercontent.com/jabawack81/pi_analytics_dashboard/main/scripts/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

### **What the installer does:**
1. ✅ Installs system dependencies (Python, Node.js, Chromium)
2. ✅ Clones the repository
3. ✅ Sets up Python virtual environment
4. ✅ Builds React frontend
5. ✅ Creates systemd services
6. ✅ Configures kiosk mode
7. ✅ Sets up OTA updates

## ⚙️ Configuration

### **1. PostHog Credentials**
```bash
nano ~/posthog_pi/backend/.env
```

Add your PostHog details:
```env
POSTHOG_API_KEY=your_api_key_here
POSTHOG_PROJECT_ID=your_project_id_here
POSTHOG_HOST=https://app.posthog.com
```

### **2. Start Services**
```bash
sudo systemctl start posthog-display.service
sudo systemctl status posthog-display.service
```

### **3. Access Dashboard**
- **Dashboard**: `http://raspberry-pi-ip:5000`
- **Configuration**: `http://raspberry-pi-ip:5000/config`
- **In Kiosk Mode**: Press `Ctrl+Shift+C` for config

## 🔧 Manual Installation (Alternative)

If you prefer manual setup:

### **1. Clone Repository**
```bash
git clone https://github.com/jabawack81/pi_analytics_dashboard.git
cd pi_analytics_dashboard
```

### **2. Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your PostHog credentials
```

### **3. Frontend Setup**
```bash
cd ../frontend
npm install
npm run build
```

### **4. Run Application**
```bash
cd ../backend
source venv/bin/activate
python app.py
```

## 📱 HyperPixel Round Display Setup

For the round display, run the display configuration:

```bash
sudo ~/posthog_pi/config/hyperpixel-setup.sh
sudo reboot
```

## 🔄 OTA Updates

### **Enable OTA**
1. Go to `http://pi-ip:5000/config`
2. Click "Updates" tab
3. Enable OTA updates
4. Select branch (main/dev/canary)
5. Save configuration

### **Manual Updates**
```bash
# Check for updates
curl http://localhost:5000/api/admin/ota/check

# Update system
curl -X POST http://localhost:5000/api/admin/ota/update
```

## 🛠️ Troubleshooting

### **Service Status**
```bash
sudo systemctl status posthog-display.service
sudo journalctl -u posthog-display.service
```

### **Check Logs**
```bash
tail -f /var/log/posthog-pi/ota.log
```

### **Test Configuration**
```bash
# Test PostHog connection
curl http://localhost:5000/api/health
curl http://localhost:5000/api/stats
```

### **Restart Services**
```bash
sudo systemctl restart posthog-display.service
```

## 🎯 Access Points

- **Dashboard**: `http://pi-ip:5000`
- **Configuration**: `http://pi-ip:5000/config`
- **API Health**: `http://pi-ip:5000/api/health`
- **API Stats**: `http://pi-ip:5000/api/stats`

## 🔧 Development Mode

For development with file watching:

```bash
cd posthog_pi
python dev.py
```

This starts both React dev server and Flask in debug mode.

## 📋 System Requirements

- Raspberry Pi 3B+ or newer
- 8GB+ SD card
- Internet connection
- (Optional) HyperPixel Round display

## 🆘 Support

Check the following if you encounter issues:

1. **Network**: Ensure Pi has internet access
2. **PostHog**: Verify API credentials in `.env`
3. **Services**: Check systemd service status
4. **Logs**: Review application logs
5. **Permissions**: Ensure correct file permissions

### Network Management

For advanced network troubleshooting, use the network manager script:

```bash
# Check network status
python3 scripts/network-manager.py status

# Scan for available WiFi networks
python3 scripts/network-manager.py scan

# Start access point mode for setup
python3 scripts/network-manager.py start-ap

# Stop access point mode
python3 scripts/network-manager.py stop-ap

# Ensure network is properly configured
python3 scripts/network-manager.py ensure-setup
```

The network manager handles:
- WiFi access point setup (SSID: `Pi-Analytics-Setup`)
- Network detection and connection
- Fallback to AP mode when no network available
- Automatic network transitions

## 🎉 Success!

Once installed, your PostHog Pi will:
- ✅ Auto-start on boot
- ✅ Display analytics dashboard
- ✅ Auto-update from Git
- ✅ Provide web configuration
- ✅ Run in kiosk mode

Press `Ctrl+Shift+C` in kiosk mode to access configuration!