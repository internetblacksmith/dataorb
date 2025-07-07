# PostHog Pi

IoT analytics dashboard displaying PostHog data on a Raspberry Pi with HyperPixel Round display.

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

Copy `backend/.env.example` to `backend/.env` and configure:
```
POSTHOG_API_KEY=your_api_key_here
POSTHOG_PROJECT_ID=your_project_id_here
POSTHOG_HOST=https://app.posthog.com
```

## API Endpoints

- `GET /api/stats` - PostHog statistics
- `GET /api/health` - Health check
- `GET /` - React dashboard application