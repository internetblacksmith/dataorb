# DataOrb OTA (Over-The-Air) Update System

Automatic updates via Git branches with backup and rollback support.

## Architecture

- **Backend API**: Flask endpoints for managing updates (all require admin auth)
- **Frontend UI**: Web interface in the `/config` Updates tab
- **Boot Service**: Systemd service for automatic boot-time updates
- **Git Integration**: Uses git branches (main, dev, canary) for version control

## Branch Strategy

- **main**: Stable production releases
- **dev**: Development branch with latest features
- **canary**: Experimental builds for testing

## API Endpoints

All OTA endpoints require `Authorization: Bearer <token>`. Get a token from `GET /api/auth/token` (localhost only).

### OTA Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/ota/status` | Current OTA status |
| GET | `/api/admin/ota/check` | Check for available updates |
| POST | `/api/admin/ota/update` | Pull latest updates |
| POST | `/api/admin/ota/switch-branch` | Switch to different branch |
| GET | `/api/admin/ota/branches` | List available remote branches |
| GET | `/api/admin/ota/test-connection` | Test git remote connectivity |
| GET | `/api/admin/ota/history` | Update log history |
| POST | `/api/admin/ota/clean-cache` | Clean git cache |

### Backup & Rollback

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/ota/backups` | List available backups |
| POST | `/api/admin/ota/rollback` | Rollback to a backup tag |

Backups are created automatically before each update.

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/ota/config` | Get OTA configuration |
| POST | `/api/admin/ota/config` | Update OTA configuration |
| POST | `/api/admin/ota/update-cron` | Update the cron schedule |

### Configuration Options

```json
{
  "ota": {
    "enabled": true,
    "branch": "main",
    "check_on_boot": true,
    "auto_pull": false,
    "update_schedule": "0 3 * * *",
    "backup_before_update": true,
    "max_backups": 5,
    "last_update": null,
    "last_check": null
  }
}
```

## Web UI

1. Access `/config` (or `Ctrl+Shift+C` in kiosk mode)
2. Navigate to "Updates" tab
3. Enable OTA, select branch, configure auto-update behavior
4. Save configuration

## Installation

```bash
sudo ./scripts/install-ota-service.sh
```

This installs a systemd service for boot-time update checks.

## Troubleshooting

### Service Status
```bash
sudo systemctl status pi-analytics-backend
sudo journalctl -u pi-analytics-backend --no-pager -n 50
```

### Manual Update Check
```bash
cd ~/dataorb
python3 scripts/boot-update.py
```

### API-based Update
```bash
TOKEN=$(curl -s http://localhost:5000/api/auth/token | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/admin/ota/check
curl -X POST -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/admin/ota/update
```

## File Structure

```
dataorb/
├── backend/
│   ├── config_manager.py          # Configuration management
│   ├── ota_manager.py             # OTA operations (git pull, backup, rollback)
│   └── app.py                     # Flask app with OTA endpoints
├── frontend/src/components/
│   └── ConfigPage/OTAConfig.tsx   # OTA configuration UI
├── scripts/
│   ├── boot-update.py             # Boot update script
│   └── install-ota-service.sh     # Service installation
└── config/
    └── posthog-pi-ota.service     # Systemd service file
```

## Recovery

If the system becomes unresponsive after an update:

1. Connect keyboard/mouse to device
2. Switch to TTY (`Ctrl+Alt+F1`)
3. Rollback via git:

```bash
cd ~/dataorb
git tag -l backup-*                        # List backups
git reset --hard backup-YYYYMMDD-HHMMSS    # Rollback
sudo systemctl restart pi-analytics-backend pi-analytics-display
```

## Security

- All OTA endpoints require admin authentication
- Branch names are validated against `^[a-zA-Z0-9][a-zA-Z0-9._/-]*$`
- Git repository should use HTTPS or SSH keys
- Backups are created automatically before updates
