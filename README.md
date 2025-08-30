# DataOrb

IoT dashboard displaying PostHog analytics on a Raspberry Pi with HyperPixel Round display.

**Note:** This is an independent project, not affiliated with PostHog.

## Features

- Real-time PostHog analytics on a circular 480x480 display
- Four dashboard layouts: Classic, Modern, Analytics, Executive
- Theme system with dark/light modes and custom branding
- Web-based configuration interface at `/config`
- Auto-refresh when config changes via filesystem watcher
- Ansible-automated deployment with WiFi Access Point setup
- OTA updates with rollback support

## Hardware Requirements

- **Raspberry Pi** — Pi Zero 2 W recommended (Pi 3/4/5 also supported)
- **Display** — HyperPixel 2.1 Round (480x480) or Waveshare 3.4" HDMI (800x800)
- **MicroSD Card** — 8GB minimum, 16GB+ recommended
- **Power Supply** — 5V 2.5A+

See [docs/hardware.md](docs/hardware.md) for the full compatibility matrix and OS selection guide.

## Quick Start

```bash
# Interactive menu with all available commands
make

# Or run specific targets
make rebuild     # Clean + install + build
make dev         # Start development servers
make lint        # Run all linters
make test        # Run tests
make deploy      # Build locally and deploy to Pi
```

### Manual Development

```bash
# Start both React file watcher and Flask dev server
python3 dev.py
```

### Manual Production Build

```bash
./build.sh
cd backend
source venv/bin/activate
python3 app.py
```

## Configuration

### PostHog API Credentials

Configure via the web interface at `http://<pi-ip>:5000/config` (PostHog tab), or manually:

```bash
cd backend
cp device_config.example.json device_config.json
# Edit device_config.json with your PostHog API key and Project ID
```

### Device Settings

All settings are managed through `backend/device_config.json`:
- Display metrics and layout configuration
- OTA update settings
- Network configuration

Access via the web interface at `/config`.

## Documentation

| Topic | Guide |
|-------|-------|
| API Reference | [docs/api.md](docs/api.md) |
| Architecture | [docs/ARCHITECTURE_DECISIONS.md](docs/ARCHITECTURE_DECISIONS.md) |
| Hardware & OS | [docs/hardware.md](docs/hardware.md) |
| OTA Updates | [docs/OTA_README.md](docs/OTA_README.md) |
| Quick Start | [docs/QUICK_START.md](docs/QUICK_START.md) |
| Pi 5 Setup | [docs/PI5_SETUP.md](docs/PI5_SETUP.md) |

## License

[MIT](LICENSE)
