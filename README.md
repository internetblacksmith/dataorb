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

## Tested Hardware Compatibility Matrix

### ⚠️ Important Display Notice
**HyperPixel Round is END OF LIFE** - This display is no longer manufactured by Pimoroni. It was used for this project as it was the only round display available to the developer. The HyperPixel drivers have not been updated for newer OS versions, requiring **Raspberry Pi OS Bullseye (Legacy)** or older. For new projects, consider using HDMI displays instead.

| Raspberry Pi Model | HyperPixel Round (480x480)* | Waveshare 3.4" HDMI (800x800) | Generic HDMI |
|-------------------|----------------------------|--------------------------------|--------------|
| **Pi Zero W**     | ⚠️ Untested                | ❌ Not Supported               | ⚠️ Untested  |
| **Pi Zero 2 W**   | ✅ **Working***            | ⚠️ Untested                    | ⚠️ Untested  |
| **Pi 3 B/B+**     | ⚠️ Untested                | ⚠️ Untested                    | ⚠️ Untested  |
| **Pi 4**          | ⚠️ Untested                | ⚠️ Untested                    | ⚠️ Untested  |
| **Pi 5**          | ⚠️ Untested                | ⚠️ Untested                    | ⚠️ Untested  |

*Requires Raspberry Pi OS Bullseye (Legacy) - newer OS versions not supported by HyperPixel drivers

### Legend
- ✅ **Working** - Tested and confirmed working with ansible playbook
- ⚠️ **Untested** - Should work but not yet verified
- ❌ **Not Supported** - Known incompatibility or insufficient resources

### Verified Configurations
- **Pi Zero 2 W + HyperPixel Round**: Fully tested on Bullseye (Legacy), stable performance
  - ⚠️ **OS Requirement**: Must use Raspberry Pi OS Bullseye (2021-2022 releases) or older
  - ❌ **Not compatible** with Bookworm (2023+) due to driver incompatibility

### Notes
- **HyperPixel limitations**: End-of-life product, requires Legacy OS, no driver updates available
- Pi Zero W has limited RAM (512MB) and single-core CPU - may struggle with modern browsers
- Waveshare HDMI displays require more GPU memory, recommended for Pi 3/4/5 only
- HyperPixel uses GPIO/DPI interface, leaving HDMI port free for debugging
- For new deployments, HDMI displays are recommended for better OS compatibility

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

### Using the Makefile (Recommended)

The project includes a comprehensive Makefile for all common operations:

```bash
# Show interactive menu (default)
make

# Complete rebuild (clean + install + build)
make rebuild

# Rebuild specific components
make frontend    # Frontend only
make backend     # Backend only

# Service management
make restart     # Restart all services
make status      # Check service status
make logs        # View recent logs
make logs-follow # Follow logs in real-time

# Development
make dev         # Instructions for dev mode
make lint        # Run code linting
make format      # Auto-format code
```

### Manual Development Mode
```bash
# Start both React file watcher and Flask dev server
python3 dev.py
```

### Manual Production Build
```bash
# Build and run integrated application
./build.sh
cd backend
source venv/bin/activate
python3 app.py
```

## Configuration

### PostHog API Configuration
The PostHog API credentials are configured through the web interface at `/config` or by editing `backend/device_config.json`:

1. **Via Web Interface (Recommended)**:
   - Navigate to `http://<pi-ip>:5000/config`
   - Go to the "PostHog" tab
   - Enter your API key and Project ID
   - Click "Save Changes"

2. **Manual Configuration**:
   ```bash
   cd backend
   cp device_config.example.json device_config.json
   # Edit device_config.json with your PostHog credentials
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
- `GET /api/config/version` - Config version hash (for auto-reload)
- `GET /` - React dashboard application
- `GET /config` - Web configuration interface
- OTA endpoints - see `OTA_README.md` for details

## Features

### Automatic Config Reload
The dashboard automatically reloads when configuration changes are made via the web interface:
- Frontend polls `/api/config/version` every 5 seconds
- When config hash changes, page automatically refreshes
- No manual intervention needed after saving settings
- Works with all configuration changes (layout, metrics, themes, etc.)

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