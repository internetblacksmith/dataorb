# PostHog Pi OTA (Over-The-Air) Update System

This document describes the OTA update system for PostHog Pi, which allows for automatic updates using Git branches.

## Architecture Overview

The OTA system consists of:
- **Backend API**: Flask endpoints for managing updates
- **Frontend UI**: Web interface for configuring OTA settings
- **Boot Service**: Systemd service for automatic boot-time updates
- **Git Integration**: Uses git branches (main, dev, canary) for version control

## Branch Strategy

- **main**: Stable production releases
- **dev**: Development branch with latest features
- **canary**: Experimental builds for testing

## Features

### 1. Web Configuration Interface
- Access via `/config` or `Ctrl+Shift+C` in kiosk mode
- Branch selection dropdown
- Enable/disable OTA updates
- Configure automatic update behavior

### 2. API Endpoints

#### OTA Management
- `GET /api/admin/ota/status` - Get current OTA status
- `GET /api/admin/ota/check` - Check for available updates
- `POST /api/admin/ota/update` - Pull latest updates
- `POST /api/admin/ota/switch-branch` - Switch to different branch
- `POST /api/admin/ota/reset` - Hard reset to remote branch

#### Backup & Rollback
- `GET /api/admin/ota/backups` - List available backups
- `POST /api/admin/ota/backup` - Create backup
- `POST /api/admin/ota/rollback` - Rollback to backup

#### Configuration
- `GET /api/admin/ota/config` - Get OTA configuration
- `POST /api/admin/ota/config` - Update OTA configuration

### 3. Automatic Updates

#### Boot-time Updates
- Systemd service runs on boot
- Checks for updates if enabled
- Automatically pulls updates if configured
- Logs all operations

#### Configuration Options
- `enabled`: Enable/disable OTA system
- `branch`: Target branch (main, dev, canary)
- `check_on_boot`: Check for updates on boot
- `auto_pull`: Automatically pull updates
- `last_update`: Timestamp of last update
- `last_check`: Timestamp of last check

## Installation

### 1. Install OTA Service
```bash
# Install systemd service for boot-time updates
sudo ./scripts/install-ota-service.sh
```

### 2. Configure Git Repository
Ensure your device's project folder is a git repository:
```bash
cd /path/to/posthog_pi
git remote add origin https://github.com/yourusername/posthog_pi.git
git fetch origin
```

### 3. Enable OTA Updates
1. Access configuration page at `http://device-ip:5000/config`
2. Navigate to "Updates" tab
3. Enable OTA updates
4. Select target branch
5. Configure automatic update behavior
6. Save configuration

## Usage

### Manual Updates
1. Access configuration page
2. Go to "Updates" tab
3. Click "Check for Updates"
4. Click "Update System" if updates are available

### Branch Switching
1. Select desired branch from dropdown
2. System will automatically switch and pull updates
3. Application will restart with new version

### Backup and Rollback
- Backups are automatically created before updates
- Manual backups can be created via API
- Rollback to any backup tag if needed

## Security Considerations

- OTA updates require network access
- Git repository should use HTTPS or SSH keys
- Consider firewall rules for git operations
- Backup system protects against failed updates

## Troubleshooting

### Check Service Status
```bash
sudo systemctl status posthog-pi-ota
```

### View Logs
```bash
sudo journalctl -u posthog-pi-ota
```

### Manual Update Check
```bash
cd /path/to/posthog_pi
python3 scripts/boot-update.py
```

### Reset to Remote Branch
```bash
curl -X POST http://localhost:5000/api/admin/ota/reset \
  -H "Content-Type: application/json" \
  -d '{"branch": "main"}'
```

## File Structure

```
posthog_pi/
├── backend/
│   ├── config_manager.py      # Configuration management
│   ├── ota_manager.py         # OTA operations
│   └── app.py                 # Flask app with OTA endpoints
├── frontend/src/
│   └── ConfigPage.tsx         # UI for OTA configuration
├── scripts/
│   ├── boot-update.py         # Boot update script
│   └── install-ota-service.sh # Service installation
├── config/
│   └── posthog-pi-ota.service # Systemd service file
└── OTA_README.md              # This file
```

## Logs and Monitoring

### Log Files
- `/var/log/posthog-pi/ota.log` - OTA operations log
- `journalctl -u posthog-pi-ota` - Systemd service logs

### Status Monitoring
- Check last update time in configuration
- Monitor git branch and commit via API
- View system health in configuration UI

## Configuration File

The OTA configuration is stored in `device_config.json`:

```json
{
  "ota": {
    "enabled": true,
    "branch": "main",
    "check_on_boot": true,
    "auto_pull": true,
    "last_update": "2023-12-01T10:30:00Z",
    "last_check": "2023-12-01T10:30:00Z"
  }
}
```

## Best Practices

1. **Testing**: Use canary branch for testing new features
2. **Staging**: Use dev branch for development work
3. **Production**: Use main branch for stable releases
4. **Backups**: Regular backups before major updates
5. **Monitoring**: Check logs regularly for failed updates
6. **Network**: Ensure stable internet connection for updates

## Recovery

If the system becomes unresponsive after an update:

1. **Physical Access**: Connect keyboard/mouse to device
2. **Terminal Access**: Switch to TTY (`Ctrl+Alt+F1`)
3. **Rollback**: Use git commands to rollback
4. **Service Restart**: Restart the PostHog Pi service

```bash
# Emergency rollback
cd /path/to/posthog_pi
git tag -l backup-*  # List backups
git reset --hard backup-YYYYMMDD-HHMMSS  # Rollback
sudo systemctl restart posthog-display.service
```