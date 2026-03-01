# DataOrb - Project Context & History

This document captures the complete context of the DataOrb IoT dashboard project development.

## Project Overview

**Goal**: Build an IoT device to display PostHog analytics on a Raspberry Pi Zero W with a round HyperPixel display that boots into Chrome kiosk mode.

**Hardware**: 
- Raspberry Pi Zero W
- HyperPixel Round Display (480x480 pixels)
- Source: https://shop.pimoroni.com/products/hyperpixel-round?variant=39381081882707

## Architecture Evolution

### Initial Design
- **Backend**: Python Flask API fetching PostHog data
- **Frontend**: React TypeScript app optimized for circular display
- **Display**: Chrome kiosk mode auto-start
- **Deployment**: Single integrated server

### Key Development Phases

#### Phase 1: Basic Structure
- Created Flask API with PostHog integration
- Built React frontend with TypeScript
- Implemented circular UI optimized for 480x480 round display
- Added auto-refresh and caching mechanisms

#### Phase 2: UI Optimization for Round Display
- **Challenge**: User wanted UI optimized specifically for the circular HyperPixel Round display
- **Solution**: Complete redesign with:
  - Circular container perfectly sized for 480x480
  - Center logo with "PostHog Analytics"
  - Three stat circles positioned at top, left, right
  - Event dots around the circle perimeter
  - Bottom status indicator and timestamp
  - Rotating progress rings for visual appeal

#### Phase 3: Brand Colors Implementation
- **Challenge**: User wanted authentic PostHog brand colors
- **Research**: Found official PostHog brand palette:
  - Primary Orange: `#f44c04` (244, 76, 4)
  - Primary Blue: `#6e8cf9` (110, 140, 249)
  - Dark Red/Brown: `#822802` (130, 40, 2)
  - Purple: `#987cb0` (152, 124, 176)
  - Light Gray: `#b4b4b4` (180, 180, 180)
  - Dark Gray: `#444444` (68, 68, 68)
- **Implementation**: Applied throughout design with gradients and glow effects

#### Phase 4: Development Workflow
- **Challenge**: User wanted efficient development with file watching
- **Solution**: Created comprehensive dev environment:
  - `dev.py` - Integrated development server
  - React file watching with chokidar
  - Flask auto-reload
  - Build scripts and convenience tools

#### Phase 5: Server Integration
- **Challenge**: User preferred single server instead of separate frontend/backend
- **Solution**: Flask serves both API and React build files
  - Single port (5000) for everything
  - Simplified deployment
  - Better resource usage for Pi

#### Phase 6: IoT Configuration Interface
- **Challenge**: User wanted it to be a "real IoT device" with web configuration
- **Solution**: Complete configuration system:
  - Web-based admin interface at `/config`
  - Multi-tab configuration (Device, PostHog, Display, Network, Advanced)
  - Persistent JSON configuration storage
  - API validation and testing
  - System monitoring and device info
  - Hidden access methods (Ctrl+Shift+C, click area)

#### Phase 7: WiFi Access Point Setup (COMPLETED)
- **Challenge**: Need WiFi AP mode for initial setup when no network available
- **Solution**: Complete first-boot network management system:
  - Auto-detect network availability on boot
  - Start access point if no network configured/available
  - Display setup instructions on screen with setup wizard
  - Allow web configuration through AP connection
  - Automatic switch to normal mode after WiFi configuration
  - Systemd service for boot-time network management
  - Real-time network monitoring and mode switching

## Technical Architecture

### Backend (`/backend`)
- **Flask Application** (`app.py`): Main server with API endpoints
- **Configuration Manager** (`config_manager.py`): Persistent settings storage
- **PostHog Integration**: Dynamic API configuration
- **Device Monitoring**: System performance metrics
- **API Endpoints**:
  - `/api/stats/<layout>` - PostHog analytics per layout (classic, modern, analytics, executive)
  - `/api/config/version` - Config hash for change detection
  - `/api/admin/config` - Full device configuration (GET/POST/DELETE, requires auth)
  - `/api/admin/config/validate/posthog` - Connection testing (requires auth)
  - `/api/network/status` - Network and AP mode status

### Frontend (`/frontend`)
- **Dashboard Router** (`components/DashboardRouter`): Routes to the active layout
- **Dashboard Layouts**: Classic, Modern, Analytics, Executive (`components/Dashboard*`)
- **Configuration Interface** (`components/ConfigPage`): Web admin panel
- **Setup Wizard** (`components/SetupPage`): First-boot WiFi configuration
- **Shared Hooks**: Generic `useDashboardStats<T>`, `useThemeData`, `useDisplayConfig`
- **Access Methods**: Multiple ways to enter config mode

### Configuration System
- **JSON Storage**: Persistent device settings
- **Sections**: Device, PostHog, Display, Network, Advanced
- **Validation**: Real-time API testing
- **Security**: Credential masking and validation

### Hardware Integration (`/config`, `/scripts`)
- **HyperPixel Setup**: Display driver configuration
- **Kiosk Mode**: Auto-start Chrome in fullscreen
- **Network Management**: WiFi and Access Point control
- **Systemd Services**: Boot-time startup and network management
- **Build Scripts**: Development and deployment tools

## Project Files Structure

```
dataorb/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── config_manager.py      # Configuration management
│   ├── ota_manager.py         # OTA update operations
│   ├── themes.py              # Built-in theme definitions
│   └── requirements.txt       # Python dependencies
├── frontend/src/
│   ├── components/
│   │   ├── DashboardRouter/   # Routes to active layout
│   │   ├── DashboardClassic/  # Classic 3-metric layout
│   │   ├── DashboardModern/   # Modern 6-metric layout
│   │   ├── DashboardAnalytics/# Analytics 4-metric layout
│   │   ├── DashboardExecutive/# Executive compass layout
│   │   ├── ConfigPage/        # Web configuration interface
│   │   └── SetupPage/         # WiFi setup wizard
│   ├── hooks/                 # useDashboardStats, useThemeData, etc.
│   ├── types/                 # TypeScript type definitions
│   └── utils/                 # formatNumber, formatTime, etc.
├── config/
│   └── hyperpixel-setup.sh    # Display hardware setup
├── scripts/
│   ├── network-manager.py     # WiFi and AP management
│   ├── network-boot.py        # Boot-time network setup
│   ├── boot-update.py         # OTA boot-time update check
│   └── start-kiosk.sh         # Kiosk mode startup
├── ansible/                   # Ansible playbook for Pi provisioning
├── dev.py                     # Development server
├── build.sh                   # Build script
└── Makefile                   # All project commands
```

## Development Commands

### Development Mode (File Watching)
```bash
python3 dev.py
```
- Builds React and watches for changes
- Starts Flask in debug mode with auto-reload
- Single command for full development environment

### Production Build
```bash
./build.sh
cd backend
source venv/bin/activate
python3 app.py
```

### Configuration Access
- URL: `http://localhost:5000/config`
- Keyboard: `Ctrl+Shift+C`  
- Hidden: Click 5 times in top-left corner

### Setup Access (First Boot)
- URL: `http://192.168.4.1:5000/setup` (in AP mode)
- Automatic: Device shows setup page when no network configured

## Key Design Decisions

### Circular UI Optimization
- Center logo approach instead of header
- Triangular stat layout (top, left, right)
- Event dots around perimeter
- Everything fits within circular boundary

### PostHog Brand Integration
- Official color palette from brand guidelines
- Orange-to-blue gradients for primary elements
- Dark theme with purple accents
- Authentic PostHog look and feel

### IoT Device Architecture
- Web-based configuration (no physical controls needed)
- Persistent JSON configuration
- System monitoring and health
- Hidden access for security
- Complete device management through web interface

### Single Server Approach
- Flask serves both API and React app
- Simplified deployment and resource usage
- Better for Raspberry Pi constraints
- Easier maintenance and updates

## Possible Future Enhancements

- Pre-built disk images for easy deployment
- Fleet management for multiple devices
- Custom metric queries beyond the built-in set

## Technical Notes

### PostHog API Integration
- Uses personal API keys and project IDs
- Caches data for 5 minutes to reduce API calls
- Supports custom PostHog instances
- Real-time connection validation

### Display Optimization
- Perfectly sized for 480x480 circular display
- Responsive design for other screen sizes
- Dark theme optimized for visibility
- Smooth animations and transitions

### Configuration Security
- API keys and passwords are masked in responses
- Input validation and sanitization
- Error handling and recovery
- Backup and restore capabilities

### Network Management
- Automatic WiFi detection and connection
- Access Point mode with hostapd and dnsmasq
- Real-time network monitoring and switching
- Systemd service integration for boot management
- Comprehensive logging and error handling

### Development Workflow
- File watching for instant feedback
- Integrated build and serve system
- Hot reload for both React and Flask
- TypeScript for better development experience

## User Experience

### Dashboard View
- Clean, circular layout showing key metrics
- Real-time updates every 30 seconds (configurable)
- PostHog branding and colors
- Visual indicators for system status

### Configuration Experience
- Intuitive tabbed interface
- Real-time validation feedback
- System information display
- Easy network and display setup

### IoT Device Experience
- Boots directly to dashboard or setup mode
- Automatic WiFi configuration on first boot
- Hidden configuration access for advanced settings
- Web-based management with no physical interaction needed
- Professional setup wizard for non-technical users

## Challenges Solved

1. **Round Display Optimization**: Custom circular layout design
2. **Brand Authenticity**: Official PostHog color implementation
3. **Development Efficiency**: File watching and auto-reload system
4. **Server Simplification**: Single Flask server for everything
5. **IoT Configuration**: Complete web-based device management
6. **User Experience**: Hidden but accessible configuration
7. **Network Setup**: Automatic WiFi Access Point for first-boot configuration

## Technologies Used

- **Backend**: Python, Flask, Requests, subprocess
- **Frontend**: React, TypeScript, CSS3
- **Hardware**: Raspberry Pi, HyperPixel Round Display
- **System**: Linux, systemd, Chrome kiosk mode
- **Network**: hostapd, dnsmasq, wpa_supplicant, iwconfig
- **Development**: Node.js, Chokidar, Development servers
- **Configuration**: JSON storage, REST API

This project represents a complete IoT dashboard solution with professional-grade configuration management, automatic network setup, and authentic PostHog branding, optimized specifically for circular displays. The device can be deployed as a true "plug-and-play" IoT device with web-based first-boot configuration.