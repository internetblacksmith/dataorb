# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PostHog Pi is an IoT dashboard project that displays PostHog analytics on a Raspberry Pi Zero W with HyperPixel Round display. The system boots into Chrome kiosk mode showing real-time analytics.

## Architecture

- **Integrated Server**: Single Flask app serves both API and React frontend
- **Backend**: Flask API (Python) that fetches PostHog data via REST API
- **Frontend**: React TypeScript app optimized for 480x480 round display
- **Display**: Chrome kiosk mode with systemd service auto-start
- **Hardware**: Raspberry Pi Zero W + HyperPixel Round display

## Common Development Commands

### Development Mode (File Watching)
```bash
# Start both React file watcher and Flask dev server
python3 dev.py
```
This automatically:
- Builds React and watches for file changes
- Starts Flask in debug mode with auto-reload
- Rebuilds React when you edit files
- Restarts Flask when you edit Python files

### Production Build
```bash
# Build and run everything
./build.sh
cd backend
source venv/bin/activate
python3 app.py  # Serves both API and React on port 5000
```

### Quick Production Run
```bash
# Auto-build and run
python3 run.py
```

### Manual Development Steps
```bash
# Build frontend with file watching
cd frontend
npm run dev  # Builds and watches for changes

# In another terminal - run Flask dev server
cd backend
source venv/bin/activate
FLASK_DEBUG=1 python3 app.py
```

### Testing
```bash
# Health check
curl http://localhost:5000/api/health

# Visit complete app
open http://localhost:5000
```

## Key Configuration Files

- `backend/.env` - PostHog API credentials (copy from .env.example)
- `config/hyperpixel-setup.sh` - Display hardware configuration
- `scripts/start-kiosk.sh` - Kiosk mode startup script
- `/etc/systemd/system/posthog-display.service` - Auto-start service

## Deployment Process

1. Install dependencies: `sudo ./scripts/install-deps.sh`
2. Configure PostHog API: Edit `backend/.env`
3. Set up display: `sudo ./config/hyperpixel-setup.sh`
4. Reboot system for kiosk mode auto-start

## PostHog Integration

The Flask API integrates with PostHog's REST API to fetch:
- Events count (24h)
- Unique users (24h)
- Page views (24h)
- Recent events list

API endpoints are cached for 5 minutes to reduce API calls.

## Display Optimization

The React frontend is specifically optimized for:
- 480x480 circular display
- Dark theme for better visibility
- Responsive grid layout
- Auto-refresh every 30 seconds
- Error handling and loading states

## Hardware-Specific Notes

- HyperPixel Round requires SPI and specific DPI timings
- Display rotation configured in /boot/config.txt
- Chrome kiosk mode with window size 480x480
- Systemd service handles auto-start and crash recovery

## Project Context Reference

For complete project context including development history, architecture details, and all features, refer to:
- `PROJECT_CONTEXT.md` - Complete development history and technical documentation
- This document contains the full story of how the project evolved through 7 major phases
- Includes all API endpoints, configuration options, and deployment details
- Essential reading for understanding the complete IoT device architecture

## Development Phases Summary

The project evolved through these key phases:
1. **Basic Structure** - Initial Flask API + React frontend
2. **Round Display UI** - Circular layout optimized for 480x480 display  
3. **PostHog Branding** - Authentic brand colors and styling
4. **Development Tools** - File watching, build scripts, dev workflow
5. **Server Integration** - Single Flask server serving both API and React
6. **IoT Configuration** - Web-based device management interface
7. **WiFi Access Point** - First-boot network setup and management

## Key Features

- **Circular Dashboard**: PostHog analytics optimized for round display
- **Real-time Updates**: 30-second refresh with 5-minute API caching
- **Web Configuration**: Hidden admin interface at `/config` or `Ctrl+Shift+C`
- **WiFi Setup**: Automatic access point mode for first-boot configuration
- **Kiosk Mode**: Auto-start Chrome in fullscreen on boot
- **Network Management**: Automatic WiFi detection and fallback to AP mode