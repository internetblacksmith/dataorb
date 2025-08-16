# Production Scripts

This folder contains **production-ready scripts** that are essential for DataOrb Pi operation.

## Core Scripts (Required for Production)

### System Management
- `wifi-ap-manager.sh` - Manages WiFi Access Point fallback when no network available
- `start-kiosk.sh` - Starts the kiosk mode display (used by systemd service)
- `boot-update.py` - Handles OTA updates during system boot
- `network-boot.py` - Network initialization and management at boot

### Documentation Management (`/docs/` subfolder)
- `check-docs.sh` - Checks documentation quality
- `detect-doc-changes.sh` - Detects when docs need updating
- `sync-docs.sh` - Syncs documentation for Docsify
- `validate-docs.sh` - Validates docs against manifest
- `preview-docs.sh` - Preview docs locally
- `skip-doc-check.sh` - Skip doc checks for specific commits

## Script Locations

```
scripts/
├── Core Production Scripts (this folder)
│   ├── wifi-ap-manager.sh
│   ├── start-kiosk.sh
│   ├── boot-update.py
│   └── network-boot.py
├── docs/
│   └── Documentation management scripts
└── ../debug/
    └── Diagnostic and testing scripts (git-ignored)
```

## Important Notes

- **Production scripts** must be thoroughly tested
- **Debug scripts** are in `/debug/` folder (git-ignored)
- Do NOT put temporary or diagnostic scripts here
- All scripts here are deployed to the Pi

## Usage on Pi

These scripts are deployed to:
```
/home/pi/pi-analytics-dashboard/scripts/
```

And are used by systemd services and the application.