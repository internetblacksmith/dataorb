# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DataOrb is an IoT dashboard that displays PostHog analytics on a Raspberry Pi Zero W with HyperPixel Round display. The system boots into kiosk mode showing real-time analytics from your PostHog account.

**Note:** This is an independent project, not affiliated with PostHog.

## 🔧 IMPORTANT: Troubleshooting Protocol

**ALWAYS consult the Known Issues & Solutions section below BEFORE attempting any fixes.**

When encountering any error:
1. First check the "Known Issues & Solutions" section for existing solutions
2. If fixing a new issue, document it immediately after resolution
3. Include: Problem description, root cause, solution, and prevention tips

## Architecture

- **Integrated Server**: Single Flask app serves both API and React frontend
- **Backend**: Flask API (Python) that fetches data from PostHog REST API
- **Frontend**: React TypeScript app optimized for 480x480 round display
- **Display**: Chrome kiosk mode with systemd service auto-start
- **Hardware**: Raspberry Pi Zero W + HyperPixel Round display
- **OTA Updates**: Git-based over-the-air update system with branch management

## ⚠️ CRITICAL: HyperPixel Display Complete Solution

### Solved: HyperPixel Installation Requirements

After extensive debugging (August 20-21, 2025), we discovered the exact requirements for reliable HyperPixel installation. The display now works perfectly with the ansible playbook on fresh SD cards.

#### The Core Issue:
**HyperPixel driver installation is stateful** - Simply copying files doesn't work. The driver requires:
1. **Fresh compilation** of the binary on the target system
2. **Clean configuration** without ansible markers
3. **Mandatory reboot** to load device tree overlay and connect to hardware

#### Working Solution (Verified):

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

#### Complete HyperPixel Installation Sequence (WORKING):

**The ansible playbook now implements this exact sequence for fresh SD cards:**
1. Set GL driver to Legacy BEFORE installation (critical on Bullseye)
2. Enable SPI and I2C interfaces via raspi-config
3. Install all required packages including X11 and matchbox
4. Clone and run official HyperPixel installer (compiles driver)
5. Installer adds config to /boot/config.txt
6. Create X11 config forcing fb0 output
7. **Automatic reboot via ansible** - Required for framebuffer creation
8. After reboot, display works immediately

**Key Files After Successful Installation:**
- `/boot/overlays/hyperpixel2r.dtbo` (1974 bytes - compiled overlay)
- `/usr/bin/hyperpixel2r-init` (9461 bytes - compiled binary)
- `/etc/systemd/system/hyperpixel2r-init.service`
- `/etc/X11/xorg.conf.d/99-hyperpixel.conf`
- `/boot/config.txt` with HyperPixel config at end (no ansible markers)

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

**ANSIBLE PLAYBOOK (WORKING - ansible/playbook.yml):**
The playbook now correctly handles HyperPixel installation on fresh SD cards:
1. Sets GL driver to Legacy BEFORE any display configuration
2. Enables I2C and SPI before HyperPixel installation
3. Installs all required packages (X11, matchbox, surf, fbset)
4. Clones official HyperPixel repo and runs installer
5. Installer compiles driver and adds config automatically
6. Creates X11 config to force fb0 output
7. Creates pi-analytics-display service (runs as root, targets multi-user)
8. **Automatically reboots** after installation (mandatory)
9. Display works immediately after reboot

**What Changed from Non-Working Version:**
- GL driver set BEFORE installation (was after)
- Fresh compilation of driver (not just file copy)
- Clean config append by installer (no ansible markers)
- Automatic reboot in playbook (was manual)
- Simplified - removed unnecessary cleanup for fresh cards

## 📋 Known Issues & Solutions

### Issue #1: Ansible APT 404 Errors (Package Not Found)
**Problem**: Installation fails with "404 Not Found" errors for packages like nginx, python3.11-dev
```
E: Failed to fetch http://deb.debian.org/debian/pool/main/n/nginx/nginx_1.22.1-9+deb12u1_arm64.deb  404  Not Found
```

**Root Cause**: APT package cache is stale and package versions have been updated in repositories

**Solution**:
- Force apt cache refresh: `cache_valid_time: 0`
- Use `state: latest` instead of pinned versions
- Already fixed in playbook.yml

**Prevention**: Always use latest package versions unless specific version is critical

---

### Issue #2: Display Service Fails to Start (Waveshare/HDMI)
**Problem**: pi-analytics-display.service fails with "fatal signal delivered to control process"

**Root Cause**: Display scripts and configuration only created for hyperpixel_round display type

**Solution**:
- Update all display-related conditions to include waveshare_34_hdmi
- Check conditions: `when: display_type in ['hyperpixel_round', 'waveshare_34_hdmi']`
- Already fixed in playbook.yml

**Prevention**: When adding new display types, search for all display_type conditions

---

### Issue #3: Inventory Configuration Typos
**Problem**: Playbook fails with undefined variables or wrong display configurations

**Common Typos**:
- `waveshara_34_hdmi` → `waveshare_34_hdmi` (note the 'e')
- Missing `pi_model` or `display_type` in inventory

**Solution**:
- Run validation playbook first: `ansible-playbook -i inventory.ini validate-inventory.yml`
- Check inventory.ini for typos
- Validation now built into main playbook

**Prevention**: Always run validation before deployment

---

### Issue #4: Flask Development Mode Permission Denied
**Problem**: Flask fails to start on port 80 in development mode

**Root Cause**: Port 80 requires root privileges

**Solution**:
- Check FLASK_DEBUG environment variable
- Use port 5000 for development, port 80 for production
- Already fixed in backend/app.py

**Prevention**: Always use high ports (>1024) for development

---

### Issue #5: Layout Preview Images Not Loading
**Problem**: Config page shows broken images for layout previews

**Root Cause**: Flask catch-all route intercepting image URLs

**Solution**:
- Add specific route for /layout-previews/ before catch-all
- Images renamed to use dashboard names (classic.png, modern.png, etc.)
- Already fixed in backend/app.py

**Prevention**: Test all static assets after adding new routes

---

### Issue #6: HyperPixel Display Black Screen (See detailed section above)
**Problem**: Display stays black despite successful installation

**Root Cause**: Multiple issues including GL driver, framebuffer, reboot requirement

**Solution**: See complete HyperPixel section above for comprehensive fix

**Prevention**: Follow exact installation sequence in playbook

---

### Issue #7: Config Changes Not Reflected on LCD
**Problem**: Saving configuration doesn't update the display

**Root Cause**: No mechanism to reload surf browser after config save

**Solution**:
- Send SIGHUP signal to surf browser: `pkill -HUP surf`
- Added to /api/admin/config endpoint
- Already fixed in backend/app.py

**Prevention**: Always consider display refresh when changing visible settings

---

### Issue #8: Playbook Hangs at Swap File Creation
**Problem**: Ansible playbook hangs indefinitely at "Make swap file" task on Pi 4/5

**Root Cause**: 
- Creating 1GB swap file with `dd` is very slow on SD cards
- Pi 4/5 have enough RAM (2-8GB) and don't need swap
- Task was running for all Pi models

**Solution**:
- Skip swap creation for Pi 4/5 (only create for Pi Zero W/2W)
- Reduced swap size to 512MB for faster creation
- Added `status=progress` to dd command for visibility
- Already fixed in playbook.yml

**Prevention**: 
- Always consider hardware differences between Pi models
- Use `--skip-tags swap` when running on Pi 4/5
- Check RAM with `free -h` before deciding on swap

---

### Issue #9: Waveshare LCD Black Screen  
**Problem**: Waveshare 3.4" HDMI display stays black even with power

**Root Cause**: Missing HDMI configuration in /boot/config.txt

**Solution**:
1. Add HDMI config to /boot/config.txt:
```
hdmi_group=2
hdmi_mode=87
hdmi_force_hotplug=1
hdmi_timings=800 0 68 32 200 800 0 68 32 200 0 0 0 60 0 59400000 0
disable_overscan=1
```
2. Reboot the Pi
3. Test with: `sudo fbi -d /dev/fb0 -T 1 -a /usr/share/pixmaps/raspberry-pi-logo.png`

**Prevention**: 
- Ensure playbook completes the Waveshare configuration section
- Check HDMI cable connection
- Power LCD before Pi for proper initialization

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