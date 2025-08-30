# Hardware Compatibility

## Tested Hardware Matrix

### Display Notice
**HyperPixel Round is END OF LIFE** — This display is no longer manufactured by Pimoroni. The HyperPixel drivers have not been updated for newer OS versions, requiring **Raspberry Pi OS Bullseye (Legacy)** or older. For new projects, consider using HDMI displays instead.

| Raspberry Pi Model | HyperPixel Round (480x480)* | Waveshare 3.4" HDMI (800x800) | Generic HDMI |
|-------------------|----------------------------|--------------------------------|--------------|
| **Pi Zero W**     | Untested                   | Not Supported                  | Untested     |
| **Pi Zero 2 W**   | **Working***               | Untested                       | Untested     |
| **Pi 3 B/B+**     | Untested                   | Untested                       | Untested     |
| **Pi 4**          | Untested                   | Untested                       | Untested     |
| **Pi 5**          | Untested                   | Untested                       | Untested     |

*Requires Raspberry Pi OS Bullseye (Legacy) — newer OS versions not supported by HyperPixel drivers.

### Verified Configurations
- **Pi Zero 2 W + HyperPixel Round**: Fully tested on Bullseye (Legacy), stable performance
  - Must use Raspberry Pi OS Bullseye (2021–2022 releases) or older
  - Not compatible with Bookworm (2023+) due to driver incompatibility

### Notes
- **HyperPixel limitations**: End-of-life product, requires Legacy OS, no driver updates
- Pi Zero W has limited RAM (512MB) and single-core CPU — may struggle with modern browsers
- Waveshare HDMI displays require more GPU memory, recommended for Pi 3/4/5 only
- HyperPixel uses GPIO/DPI interface, leaving HDMI port free for debugging
- For new deployments, HDMI displays are recommended for better OS compatibility

## Operating System Selection

For DataOrb to work correctly, use the correct Raspberry Pi OS image:

| Image Type | Use This For |
|------------|--------------|
| **Raspberry Pi OS Lite (32-bit)** | **RECOMMENDED** — All Pi models, especially Pi Zero W/2W |
| Raspberry Pi OS Lite (64-bit) | Pi 3/4/5 with 2GB+ RAM only |
| ~~Raspberry Pi OS Desktop~~ | **DO NOT USE** — Conflicts with kiosk mode |

### Why Lite OS?
- No desktop environment — prevents conflicts with kiosk display
- Lower RAM usage — critical for Pi Zero W/2W (512MB RAM)
- Faster boot times — no unnecessary services

### Which Architecture?
- **32-bit (armhf)**: Best for Pi Zero W, Pi Zero 2W (lower RAM usage)
- **64-bit (arm64)**: Optional for Pi 3/4/5 with 2GB+ RAM
