# DataOrb - Quick Start Guide

## Operating System Requirements

### Use Raspberry Pi OS Lite

Before starting, flash the correct OS image:

| OS Image | Compatibility | Download |
|----------|--------------|----------|
| **Raspberry Pi OS Lite (32-bit)** | All Pi models (recommended) | [Download](https://www.raspberrypi.com/software/operating-systems/) |
| Raspberry Pi OS Lite (64-bit) | Pi 3/4/5 only (more RAM usage) | [Download](https://www.raspberrypi.com/software/operating-systems/) |
| ~~Raspberry Pi OS Desktop~~ | **DO NOT USE** — interferes with kiosk mode | — |

**Why Lite?** DataOrb creates its own minimal display server. The Desktop version conflicts with kiosk mode.

## Installation

### Ansible (Recommended)

The Ansible playbook in `ansible/` handles full provisioning — OS config, dependencies, services, kiosk mode, and OTA. See the playbook README for details.

### Manual Installation

```bash
git clone https://github.com/internetblacksmith/dataorb.git
cd dataorb
```

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
npm run build
```

**Run:**
```bash
cd backend
source venv/bin/activate
python3 app.py
```

## Configuration

### PostHog Credentials

Configure via the web interface at `http://<pi-ip>/config` (PostHog tab), or manually:

```bash
cd backend
cp device_config.example.json device_config.json
# Edit device_config.json with your PostHog API key and Project ID
```

> **Note:** The app reads credentials from `device_config.json`, not `.env` files.

### Start Services

On a provisioned Pi:
```bash
sudo systemctl start pi-analytics-backend pi-analytics-display
sudo systemctl status pi-analytics-backend
```

### Access Dashboard

- **Dashboard**: `http://<pi-ip>` (port 80 in production, 5000 in dev)
- **Configuration**: `http://<pi-ip>/config`
- **Kiosk shortcut**: `Ctrl+Shift+C` opens config

## HyperPixel Round Display Setup

```bash
sudo ~/dataorb/config/hyperpixel-setup.sh
sudo reboot
```

## OTA Updates

### Via Web UI
1. Go to `http://<pi-ip>/config`
2. Click "Updates" tab
3. Enable OTA updates and select branch
4. Save configuration

### Via API

OTA endpoints require admin authentication:
```bash
# Get an auth token (localhost only)
TOKEN=$(curl -s http://localhost:5000/api/auth/token | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Check for updates
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/admin/ota/check

# Apply update
curl -X POST -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/admin/ota/update
```

## Troubleshooting

### Service Status
```bash
sudo systemctl status pi-analytics-backend
sudo systemctl status pi-analytics-display
sudo journalctl -u pi-analytics-backend --no-pager -n 50
```

### Test Configuration
```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/stats/classic
```

### Restart Services
```bash
sudo systemctl restart pi-analytics-backend pi-analytics-display
```

### Network Management

```bash
python3 scripts/network-manager.py status
python3 scripts/network-manager.py scan
python3 scripts/network-manager.py start-ap
python3 scripts/network-manager.py stop-ap
```

Falls back to AP mode (`DataOrb-Setup`) when no network is available.

## Development Mode

```bash
python3 dev.py
```

Starts both the React dev server and Flask in debug mode.

## Success

Once installed, DataOrb will:
- Auto-start on boot
- Display analytics dashboard in kiosk mode
- Auto-update from Git (if OTA enabled)
- Provide web configuration at `/config`
