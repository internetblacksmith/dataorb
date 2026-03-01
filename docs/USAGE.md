# DataOrb — User Guide

Your DataOrb is a dedicated analytics display that shows PostHog metrics on a round HyperPixel screen. This guide walks you through setup and daily use.

## What You Need

- Assembled Raspberry Pi with HyperPixel Round display
- Pre-flashed SD card (see [Quick Start](QUICK_START.md) for flashing instructions)
- 5V 2.5A+ power supply
- A WiFi network with internet access

## First Boot

Plug in your DataOrb. After a few seconds, the DataOrb logo appears on screen followed by a setup wizard. The device creates a temporary WiFi network called **DataOrb-Setup** so you can configure it from your phone or laptop.

## Step 1: Connect to the Device

1. On your phone or laptop, open WiFi settings
2. Join the network named **DataOrb-Setup**
3. Open a browser and go to **http://192.168.4.1**
4. You'll see the DataOrb setup wizard with options to connect to WiFi or configure settings

## Step 2: Connect to Your WiFi

1. Tap **Connect to WiFi Network**
2. Select your home or office network from the list (a lock icon means it requires a password)
3. Enter the WiFi password and confirm
4. You'll see a "Setup Complete!" screen with instructions to reconnect to your home WiFi
5. The **DataOrb-Setup** network disappears once connected
6. Reconnect your phone or laptop to your home WiFi, then visit **http://dataorb.local** — the device IP is also shown at the bottom of all dashboard layouts

## Step 3: Configure PostHog

Until you add your PostHog credentials, the dashboard shows demo data with a "Demo Mode" indicator.

1. From any device on the same WiFi network, open **http://dataorb.local/config**
2. Go to the **PostHog** tab
3. Enter your PostHog API key and Project ID
4. Click **Test Connection**, then **Save**
5. The dashboard switches from demo data to your live analytics

> Don't have a PostHog account? Sign up free at [posthog.com](https://posthog.com). DataOrb is an independent project, not affiliated with PostHog.

## Daily Use

Once configured, DataOrb runs unattended. It auto-starts on boot and refreshes data periodically (default: every 60 seconds).

### Dashboard Layouts

Four layouts are available, each optimized for different amounts of data:

| Layout | Metrics | Best For |
|--------|---------|----------|
| **Classic** | 3 | At-a-glance overview |
| **Modern** | 6 | Balanced detail |
| **Analytics** | 7 | Data-heavy monitoring |
| **Executive** | 8 | Comprehensive compass view |

Switch layouts from the **Display** tab in configuration, or use keyboard shortcuts on the device:

| Shortcut | Action |
|----------|--------|
| Ctrl+Alt+1 | Classic layout |
| Ctrl+Alt+2 | Modern layout |
| Ctrl+Alt+3 | Analytics layout |
| Ctrl+Alt+4 | Executive layout |
| Ctrl+Alt+5 | Open configuration |
| Ctrl+Shift+C | Open configuration (alternate) |

## Configuration

Access the configuration interface at **http://dataorb.local/config** from any device on your network, or press **Ctrl+Shift+C** on the DataOrb itself.

| Tab | What It Controls |
|-----|-----------------|
| **Device** | Device name and general settings |
| **PostHog** | API key, Project ID, connection testing |
| **Display** | Layout selection, refresh interval, theme |
| **Network** | WiFi settings, AP management |
| **Updates** | OTA updates, branch selection, rollback |

### Refresh Interval

The dashboard auto-refreshes at a configurable interval. Options: 1 minute, 5 minutes, 10 minutes, 30 minutes, 1 hour, 2 hours, or 4 hours. The minimum is 60 seconds. The device is always reachable at **http://dataorb.local** via mDNS.

## Updating Your DataOrb

DataOrb supports over-the-air (OTA) updates pulled directly from GitHub.

1. Open **http://dataorb.local/config** and go to the **Updates** tab
2. Select an update branch:

| Branch | Description |
|--------|-------------|
| **main** | Stable releases, thoroughly tested |
| **dev** | Latest features, may have minor issues |
| **canary** | Experimental features, use with caution |

3. Check for updates manually or enable automatic updates on a schedule
4. Before updating, DataOrb creates a backup — if something goes wrong, use the **Rollback** option to revert

## Changing WiFi Network

If your DataOrb loses its WiFi connection (network changed, router reset, moved to a new location), it automatically re-creates the **DataOrb-Setup** access point. Connect to it and repeat the WiFi setup from Step 1.

You can also manually change networks from the **Network** tab in configuration.

## Troubleshooting

| Symptom | Solution |
|---------|----------|
| Dashboard shows "Demo Mode" | PostHog not configured or API key is invalid — check the PostHog tab in config |
| Device not responding | Check power. Try **http://dataorb.local:5000** directly, or use the device IP shown on the dashboard footer |
| Can't find the device on the network | Try **http://dataorb.local**. If mDNS isn't supported on your OS, connect to the **DataOrb-Setup** WiFi — the device is at **192.168.4.1** |
| Update failed | Use the Rollback option in the Updates tab to revert |
| Display is blank | Verify the HyperPixel is seated properly. Check service status via SSH: `sudo systemctl status pi-analytics-backend` |

For developer troubleshooting and service management, see [Quick Start — Troubleshooting](QUICK_START.md#troubleshooting).
