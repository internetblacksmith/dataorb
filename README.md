# DataOrb - Analytics Dashboard for Raspberry Pi

IoT dashboard displaying PostHog analytics on a Raspberry Pi with HyperPixel Round display.

**Note:** This is an independent project, not affiliated with PostHog.

📚 **[View Full Documentation](https://jabawack81.github.io/pi_analytics_dashboard/)** | 🚀 **[Quick Start Guide](https://jabawack81.github.io/pi_analytics_dashboard/#/QUICK_START)**

## Features

- Real-time PostHog analytics display
- Circular UI optimized for 480x480 round display
- Modern dark theme with circular design elements
- Integrated Flask server (single port)
- Auto-refresh dashboard

## Hardware Requirements

- **Raspberry Pi** (see supported models below)
  - Pi Zero W (minimum, limited performance)
  - Pi Zero 2 W (recommended for HyperPixel)
  - Pi 3/4/5 (best performance, supports Waveshare displays)
- **Display Options:**
  - **HyperPixel 2.1 Round Touch Display** (480x480) by Pimoroni
  - **Waveshare 3.4inch HDMI Display** (800x800) - Pi 4/5 recommended
- **MicroSD Card** (8GB minimum, 16GB+ recommended)
- **Power Supply** (5V 2.5A for Pi Zero W, more for Pi 3/4/5)
- **Optional: 3D Printed Case** - [Download STL files from Cults3D](https://cults3d.com/en/design-collections/printminion/various-cases-for-hyperpixel-2-1-round-touch-display-by-pimoroni)

## Operating System Selection

### ⚠️ IMPORTANT: Choose the Right OS Image

For DataOrb to work correctly, you MUST use the correct Raspberry Pi OS image:

| Image Type | Use This For | Download |
|------------|--------------|----------|
| **Raspberry Pi OS Lite (32-bit)** | ✅ **RECOMMENDED** - All Pi models, especially Pi Zero W/2W | [Download](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-32-bit) |
| Raspberry Pi OS Lite (64-bit) | Pi 3/4/5 with 2GB+ RAM only | [Download](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-64-bit) |
| ~~Raspberry Pi OS Desktop~~ | ❌ **DO NOT USE** - Conflicts with kiosk mode | Not compatible |

### Why Lite OS?
- **No desktop environment** - Prevents conflicts with kiosk display
- **Lower RAM usage** - Critical for Pi Zero W/2W (512MB RAM)
- **Faster boot times** - No unnecessary services
- **Designed for kiosk/IoT** - Exactly what DataOrb needs

### Which Architecture?
- **32-bit (armhf)**: Best for Pi Zero W, Pi Zero 2W (lower RAM usage)
- **64-bit (arm64)**: Optional for Pi 3/4/5 with 2GB+ RAM

**Note:** If you accidentally use the Desktop version, the display will show the desktop instead of DataOrb!

## Quick Start

### Development Mode
```bash
# Start both React file watcher and Flask dev server
python3 dev.py
```

### Production Build
```bash
# Build and run integrated application
./build.sh
cd backend
source venv/bin/activate
python3 app.py
```

### Quick Production Run
```bash
# Automatically builds frontend and runs server
python3 run.py
```

## Configuration

### PostHog API Configuration
Copy `backend/.env.example` to `backend/.env` and configure with your PostHog credentials:
```
POSTHOG_API_KEY=your_api_key_here
POSTHOG_PROJECT_ID=your_project_id_here
POSTHOG_HOST=https://app.posthog.com
```

### Device Configuration
Device settings are stored in `backend/device_config.json`:
- Display metrics configuration
- OTA update settings
- Network configuration
- Access via web interface at `/config`

## API Endpoints

- `GET /api/stats` - PostHog statistics
- `GET /api/health` - Health check
- `GET /` - React dashboard application
- `GET /config` - Web configuration interface
- OTA endpoints - see `OTA_README.md` for details

## Quality Gate

This project enforces strict quality standards:
```bash
# Run all quality checks (required before committing)
./quality-check.sh
```

Quality checks include:
- Python: Black formatting, Flake8 linting, MyPy types, pytest
- Frontend: ESLint, Prettier, TypeScript, Jest tests

The quality gate ensures all code is properly formatted, linted, and tested before commits.