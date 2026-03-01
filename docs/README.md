# DataOrb - Analytics Dashboard for Raspberry Pi

IoT dashboard displaying PostHog analytics on a Raspberry Pi with HyperPixel Round display.

**Note:** This is an independent project, not affiliated with PostHog.

## Features

- Real-time PostHog analytics display
- Four dashboard layouts: Classic, Modern, Analytics, Executive
- Theme system with dark/light modes and custom branding
- Web-based configuration interface at `/config`
- Auto-refresh via config version polling
- OTA updates with backup and rollback
- WiFi Access Point mode for first-boot setup

## Hardware Requirements

- **Raspberry Pi Zero 2 W** (or Pi 3/4/5 for better performance)
- **HyperPixel 2.1 Round Touch Display** by Pimoroni (or HDMI round LCD)
- **MicroSD Card** (8GB minimum, 16GB+ recommended)
- **Power Supply** (5V 2.5A+)

## Quick Start

### Development Mode
```bash
python3 dev.py
```

### Production Build
```bash
./build.sh
cd backend
source venv/bin/activate
python3 app.py
```

## Configuration

### PostHog Credentials

Configure via the web interface at `http://<pi-ip>/config`, or manually:

```bash
cd backend
cp device_config.example.json device_config.json
# Edit device_config.json with your PostHog API key and Project ID
```

### Device Configuration

All settings are stored in `backend/device_config.json`:
- Display metrics and layout configuration
- OTA update settings
- Network configuration
- Access via web interface at `/config`

## API Endpoints

See [api.md](api.md) for the full API reference. Key endpoints:

- `GET /api/stats/<layout>` - Dashboard analytics (classic, modern, analytics, executive)
- `GET /api/health` - Health check
- `GET /api/themes` - Available themes
- `GET /api/admin/config` - Device configuration (requires auth)
- `GET /api/admin/ota/*` - OTA management (requires auth)

## Quality Checks

```bash
make lint    # Run all linters
make test    # Run quality checks
```
