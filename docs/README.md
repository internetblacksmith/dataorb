# PostHog Pi

IoT analytics dashboard displaying PostHog data on a Raspberry Pi with HyperPixel Round display.

📚 **[View Full Documentation](https://jabawack81.github.io/posthog_pi/)** | 🚀 **[Quick Start Guide](https://jabawack81.github.io/posthog_pi/#/QUICK_START)**

## Features

- Real-time PostHog analytics display
- Circular UI optimized for 480x480 round display
- PostHog brand colors and styling
- Integrated Flask server (single port)
- Auto-refresh dashboard

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
Copy `backend/.env.example` to `backend/.env` and configure:
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

# Run documentation check separately
./scripts/check-docs.sh
```

Quality checks include:
- Python: Black formatting, Flake8 linting, MyPy types, pytest
- Frontend: ESLint, Prettier, TypeScript, Jest tests
- Documentation: Up-to-date and complete documentation

**Documentation updates are MANDATORY** - treated as failing tests if not updated.