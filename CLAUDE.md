# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DataOrb is an IoT dashboard that displays PostHog analytics on a Raspberry Pi Zero W with HyperPixel Round display. The system boots into kiosk mode showing real-time analytics from your PostHog account.

**Note:** This is an independent project, not affiliated with PostHog.

## Architecture

- **Integrated Server**: Single Flask app serves both API and React frontend
- **Backend**: Flask API (Python) that fetches data from PostHog REST API
- **Frontend**: React TypeScript app optimized for 480x480 round display
- **Display**: Chrome kiosk mode with systemd service auto-start
- **Hardware**: Raspberry Pi Zero W + HyperPixel Round display
- **OTA Updates**: Git-based over-the-air update system with branch management

## ⚠️ CRITICAL: HyperPixel Display Troubleshooting History

### The LCD Display Problem Journey

We encountered persistent issues with the HyperPixel 2.1 Round display not working after ansible playbook installation. Here's the complete troubleshooting history and lessons learned:

#### Problem Timeline:
1. **Initial Issue**: LCD black screen after running ansible playbook on fresh Pi installation
2. **Symptoms**: 
   - Display backlight on but screen black
   - All services running but no visual output
   - Works when manually running HyperPixel installer

#### Root Causes Discovered:

##### 1. **Missing HyperPixel Components**
- **Problem**: Manual overlay copy wasn't sufficient
- **Fix**: Must use official HyperPixel installer (`install.sh`) which:
  - Compiles device tree overlay from source
  - Installs hyperpixel2r-init binary
  - Creates systemd service
  - Sets up proper boot configuration

##### 2. **Wrong Framebuffer Output**
- **Problem**: X server outputting to fb1 (HDMI) instead of fb0 (HyperPixel)
- **Diagnostics showed**: Two framebuffers (fb0: 480x480, fb1: 720x480)
- **Fix**: Added X11 configuration to force fb0:
  ```
  /etc/X11/xorg.conf.d/99-hyperpixel.conf
  Section "Device"
      Driver "fbdev"
      Option "fbdev" "/dev/fb0"
  ```

##### 3. **Missing Display Service**
- **Problem**: `pi-analytics-display.service` was completely missing from playbook
- **Fix**: Created service template and added to playbook

##### 4. **Service Startup Conflicts**
- **Problem**: Multiple X server instances from rc.local and systemd
- **Symptoms**: Display service inactive, X already running from rc.local
- **Fix**: 
  - Removed pi-dashboard-autostart.sh from rc.local
  - Display service now manages entire X server lifecycle
  - Changed service to run as root (permission issues)
  - Target multi-user.target (not graphical.target)

##### 5. **ARMv6 Compatibility** (Pi Zero W specific)
- **Problem**: NodeSource doesn't support ARMv6 architecture
- **Fix**: Use unofficial Node.js builds for ARMv6

##### 6. **Port 80 Conflicts**
- **Problem**: nginx blocking port 80
- **Fix**: Detect and stop nginx in playbook, add CAP_NET_BIND_SERVICE capability

##### 7. **GL Driver Incompatibility** (ROOT CAUSE OF BLACK SCREEN!)
- **Problem**: Full KMS GL driver doesn't work with HyperPixel
- **Discovery**: Everything running perfectly but display stays black
- **Fix**: MUST set GL driver to Legacy using `raspi-config nonint do_gldriver G1`
- **Verification**: `raspi-config nonint get_gldriver` should return 1
- **Note**: This was discovered from official Pimoroni documentation - HyperPixel2r is incompatible with Full KMS driver

##### 8. **Reboot Required After Installation** (CRITICAL!)
- **Problem**: X server error "no screens found" even after successful installation
- **Discovery**: HyperPixel installer completes but framebuffer devices don't exist until reboot
- **Symptoms**: `/dev/fb0` doesn't exist, X server can't find screens
- **Fix**: MUST reboot after HyperPixel installation for driver to initialize
- **Verification**: After reboot, `ls -la /dev/fb*` should show fb0 with 480x480 resolution
- **Note**: The device tree overlay only loads at boot time, creating the framebuffer devices

#### Complete HyperPixel Installation Sequence:

**The correct order is CRITICAL for success (verified with test-lcd-install.sh):**
1. Set GL driver to Legacy (or disable KMS overlays)
2. Enable SPI and I2C interfaces
3. Run official HyperPixel installer from Pimoroni GitHub
4. Create X11 config forcing fb0 output
5. Install matchbox window manager
6. **REBOOT - Required for framebuffer creation**
7. Only then can X server find screens and display work

**Source of Truth**: `scripts/test-lcd-install.sh` - This script successfully installs HyperPixel on fresh SD card

#### Diagnostic Tools Created:
- `debug/display-diagnostic.sh` - Comprehensive display troubleshooting script that checks:
  - HyperPixel components installation
  - Framebuffer devices and configuration
  - Service status and dependencies
  - X server and display processes
  - GPIO backlight status
  - Boot configuration
  - Permission issues

#### Complete HyperPixel Installation Sequence:

**The correct order is CRITICAL for success:**
1. Set GL driver to Legacy (or disable KMS overlays)
2. Enable SPI and I2C interfaces
3. Run official HyperPixel installer from Pimoroni GitHub
4. Create X11 config forcing fb0 output
5. Install matchbox window manager
6. **REBOOT - Required for framebuffer creation**
7. Only then can X server find screens and display work

#### Key Lessons for Future Display Issues:

**ALWAYS CHECK THESE FIRST:**
1. Run diagnostic: `./debug/display-diagnostic.sh`
2. **CHECK GL DRIVER**: `raspi-config nonint get_gldriver` (MUST be 1 for Legacy!)
3. Verify framebuffer exists: `ls -la /dev/fb*` (should show fb0 480x480)
   - If no fb0 after installation = REBOOT REQUIRED
4. Check X server: `ps aux | grep Xorg`
5. Service status: `systemctl status pi-analytics-display`
6. HyperPixel init: `systemctl status hyperpixel2r-init`
7. Backlight GPIO: `raspi-gpio get 19` (should be OUTPUT, level=1)

**COMMON FIXES TO TRY:**
```bash
# MOST IMPORTANT: Set GL driver to Legacy
sudo raspi-config nonint do_gldriver G1
sudo reboot

# Turn on backlight
sudo raspi-gpio set 19 op dh

# Restart services in order
sudo systemctl restart hyperpixel2r-init
sudo systemctl restart pi-analytics-backend
sudo systemctl restart pi-analytics-display

# Manual test
sudo xinit /usr/bin/surf -F http://localhost -- :0 -nocursor vt2
```

**ANSIBLE PLAYBOOK REQUIREMENTS:**
1. **CRITICAL: Must set GL driver to Legacy** (`raspi-config nonint do_gldriver G1`)
2. Must run official HyperPixel installer (not just copy files)
3. Must create X11 config to force fb0
4. Must create and enable pi-analytics-display service with matchbox window manager
5. Must NOT use rc.local for X server startup
6. Service must target multi-user.target
7. Service must run as root for X permissions
8. Must disable conflicting VC4 KMS overlays
9. **MUST REBOOT after installation** for framebuffer devices to be created

## Quality Gate Requirements

**🚨 CRITICAL**: After completing any development task, you MUST run the quality gate checks to ensure:
- All tests are passing
- Code is properly formatted and linted
- Documentation is kept up to date when making significant changes

### Running Quality Checks
```bash
# Run all quality checks (required before marking any task as complete)
./quality-check.sh

# Run specific checks:
# Backend
cd backend && source venv/bin/activate
black --check app.py config_manager.py ota_manager.py  # Python formatting
flake8 app.py config_manager.py ota_manager.py        # Python linting
mypy app.py config_manager.py ota_manager.py          # Type checking
pytest tests/ -v                                       # Python tests

# Frontend
cd frontend
npm run lint                    # ESLint
npm run format:check           # Prettier check
npm run quality                # All frontend checks

# Install pre-commit hooks (one-time setup)
./scripts/install-pre-commit.sh
```

### Documentation Management

Documentation should be updated when:
- Adding new features or APIs
- Changing configuration options
- Modifying installation or setup procedures
- Adding or removing dependencies

Use Claude Code to review if documentation needs updates based on your changes. The documentation sync script (`./scripts/docs/sync-docs.sh`) keeps the Docsify docs in sync with the main documentation files.

### Quality Tools Setup
- **Backend**: black, flake8, mypy, pytest (see `backend/requirements-dev.txt`)
- **Frontend**: ESLint, Prettier, TypeScript checks (see `frontend/package.json`)
- **Pre-commit**: Automatic checks before git commits (`.pre-commit-config.yaml`)

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

# Test OTA updates
curl http://localhost:5000/api/admin/ota/status
curl http://localhost:5000/api/admin/ota/check
```

## Key Configuration Files

- `backend/.env` - PostHog API credentials (copy from .env.example)
- `backend/device_config.json` - Device configuration including OTA settings
- `config/hyperpixel-setup.sh` - Display hardware configuration
- `scripts/start-kiosk.sh` - Kiosk mode startup script
- `scripts/install-pi.sh` - Complete Pi installation script
- `scripts/boot-update.py` - OTA update script for boot-time updates
- `/etc/systemd/system/dataorb-display.service` - Auto-start service
- `/etc/systemd/system/dataorb-pi-ota.service` - OTA update service

## Deployment Process

### Easy Installation (Recommended)
```bash
# One-command installation on fresh Raspberry Pi
curl -sSL https://raw.githubusercontent.com/jabawack81/pi_analytics_dashboard/main/scripts/install-pi.sh | bash
```

### Manual Installation
1. Install dependencies: `sudo ./scripts/install-deps.sh`
2. Configure PostHog API: Edit `backend/.env`
3. Set up display: `sudo ./config/hyperpixel-setup.sh`
4. Install OTA service: `sudo ./scripts/install-ota-service.sh`
5. Reboot system for kiosk mode auto-start

## PostHog Integration

The Flask API integrates with PostHog's REST API to fetch:
- Events count (24h)
- Unique users (24h)
- Page views (24h)
- Recent events list

API endpoints are cached for 5 minutes to reduce API calls.

## Dashboard Metrics Configuration

The dashboard displays configurable PostHog metrics in three circular positions:

### Available Metrics
- **Events (24h)**: Total events in last 24 hours
- **Users (24h)**: Unique users in last 24 hours  
- **Page Views (24h)**: Page view events in last 24 hours
- **Custom Events (24h)**: Non-pageview events in last 24 hours
- **Sessions (24h)**: Unique sessions in last 24 hours
- **Events (1h)**: Events in last hour
- **Avg Events/User**: Average events per user (24h)

### Configuration
- Access via `/config` → "Display" tab → "Dashboard Metrics"
- Configure each position (top, left, right) independently
- Enable/disable metrics per position
- Choose metric type from dropdown
- Customize display labels
- Real-time preview of changes

### Layout Positions
```
    [TOP]
[LEFT] 🟡 [RIGHT]
```

## Display Optimization

The React frontend is specifically optimized for:
- 480x480 circular display
- Dark theme for better visibility
- Responsive grid layout with configurable metrics
- Auto-refresh every 30 seconds
- Error handling and loading states

## Hardware-Specific Notes

- HyperPixel Round requires SPI and specific DPI timings
- Display rotation configured in /boot/config.txt
- Chrome kiosk mode with window size 480x480
- Systemd service handles auto-start and crash recovery

## OTA Update System

The project includes a comprehensive over-the-air update system:

### Branch Strategy
- **main**: Stable production releases
- **dev**: Development branch with latest features  
- **canary**: Experimental builds for testing

### Features
- **Web Interface**: Configure updates via `/config` → "Updates" tab
- **API Endpoints**: Programmatic control via REST API
- **Boot Updates**: Automatic update checks on system boot
- **Backup System**: Automatic backups before updates with rollback capability
- **Branch Switching**: Easy switching between main/dev/canary branches
- **Status Monitoring**: Real-time update status and history

### API Endpoints
- `GET /api/admin/ota/status` - Current OTA status
- `GET /api/admin/ota/check` - Check for updates
- `POST /api/admin/ota/update` - Apply updates
- `POST /api/admin/ota/switch-branch` - Switch branches
- `GET /api/admin/ota/backups` - List backups
- `POST /api/admin/ota/rollback` - Rollback to backup

### Configuration
OTA settings are stored in `device_config.json`:
- `enabled`: Enable/disable OTA system
- `branch`: Target branch (main/dev/canary)
- `check_on_boot`: Auto-check on boot
- `auto_pull`: Auto-apply updates
- `last_update`: Last update timestamp

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
8. **OTA Updates** - Git-based over-the-air update system with branch management

## Key Features

- **Circular Dashboard**: PostHog analytics optimized for round display
- **Real-time Updates**: 30-second refresh with 5-minute API caching
- **Web Configuration**: Hidden admin interface at `/config` or `Ctrl+Shift+C`
- **WiFi Setup**: Automatic access point mode for first-boot configuration
- **Kiosk Mode**: Auto-start Chrome in fullscreen on boot
- **Network Management**: Automatic WiFi detection and fallback to AP mode
- **OTA Updates**: Git-based updates with branch switching (main/dev/canary)
- **Automatic Backups**: Rollback capability for failed updates
- **Boot-time Updates**: Automatic update checks on system boot
- **One-click Installation**: Complete setup script for fresh Raspberry Pi