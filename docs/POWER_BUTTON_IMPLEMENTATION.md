# Power Button Implementation for DataOrb with HyperPixel Display

## Problem Statement
The HyperPixel Round display uses all GPIO pins, making traditional GPIO-based power button implementations challenging. We need a solution that:
- Provides safe shutdown functionality
- Allows wake from halt/shutdown state
- Works with the limited I2C pins available on the HyperPixel

## Recommended Solution: Hybrid I2C + RUN Header Approach

### Hardware Components Required
1. **Momentary push button** (normally open)
2. **MCP23017 I2C GPIO Expander** (optional, for additional functionality)
3. **1N4148 diode** (if using GPIO3 wake functionality)
4. **10kΩ pull-up resistor** (optional)
5. **2-pin header for RUN pins** (if not already populated on Pi Zero)

### Solution Architecture

#### Option 1: Simple RUN Header Solution (Recommended)
This is the simplest and most reliable solution for basic on/off functionality.

**Hardware Setup:**
1. Solder a 2-pin header to the RUN pads on the Pi Zero (located near the camera connector)
2. Connect a momentary push button between the two RUN pins
3. Use the alternate I2C bus (i2c-3) on the HyperPixel for shutdown detection

**How it works:**
- **Power ON**: When Pi is halted, pressing the button shorts the RUN pins, causing a CPU reset and boot
- **Shutdown**: Monitor button via I2C and trigger safe shutdown via software

#### Option 2: I2C-Based Button with RUN Header Wake
This provides more flexibility and allows for multiple buttons.

**Hardware Setup:**
```
MCP23017 Connection (to HyperPixel I2C breakout):
- VDD → 3.3V
- VSS → GND
- SCL → BCM11 (i2c-3 SCL on HyperPixel breakout)
- SDA → BCM10 (i2c-3 SDA on HyperPixel breakout)
- A0, A1, A2 → GND (sets address to 0x20)
- RESET → 3.3V (through 10kΩ resistor)

Button Connections:
- Power Button → MCP23017 GPA0 and GND
- Additional buttons → Other MCP23017 GPIO pins

Wake Circuit:
- Momentary button → RUN header pins
```

### Software Implementation

#### 1. Enable Alternate I2C Bus
```bash
# Add to /boot/config.txt
dtparam=i2c_vc=on
dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=10,i2c_gpio_scl=11

# Verify I2C bus is available
i2cdetect -y 3
```

#### 2. Python Power Button Monitor Script
```python
#!/usr/bin/env python3
"""
Power button monitor for DataOrb using MCP23017
Monitors button press on alternate I2C bus and triggers safe shutdown
"""

import time
import subprocess
import smbus
from threading import Thread

# MCP23017 Registers
IODIRA = 0x00  # I/O direction register A
GPPUA = 0x0C   # Pull-up register A
GPIOA = 0x12   # GPIO register A

class PowerButtonMonitor:
    def __init__(self, bus=3, address=0x20):
        self.bus = smbus.SMBus(bus)
        self.address = address
        self.running = True
        self.button_pressed_time = None
        
        # Configure MCP23017
        self.setup_mcp23017()
        
    def setup_mcp23017(self):
        """Configure MCP23017 for button input"""
        # Set GPA0 as input (1), others as output (0)
        self.bus.write_byte_data(self.address, IODIRA, 0x01)
        # Enable pull-up on GPA0
        self.bus.write_byte_data(self.address, GPPUA, 0x01)
        
    def read_button(self):
        """Read button state from MCP23017"""
        try:
            # Read GPIOA register
            state = self.bus.read_byte_data(self.address, GPIOA)
            # Button pressed when GPA0 is LOW (0)
            return (state & 0x01) == 0
        except:
            return False
            
    def monitor_button(self):
        """Monitor button for shutdown trigger"""
        while self.running:
            if self.read_button():
                if self.button_pressed_time is None:
                    self.button_pressed_time = time.time()
                    print("Power button pressed...")
                    
                # Check for long press (3 seconds)
                if time.time() - self.button_pressed_time >= 3:
                    print("Long press detected - shutting down...")
                    self.shutdown()
                    self.running = False
            else:
                if self.button_pressed_time is not None:
                    press_duration = time.time() - self.button_pressed_time
                    if press_duration < 3:
                        print(f"Short press ({press_duration:.1f}s) - ignored")
                    self.button_pressed_time = None
                    
            time.sleep(0.1)
            
    def shutdown(self):
        """Perform safe shutdown"""
        try:
            # Optional: Save any application state here
            print("Performing safe shutdown...")
            subprocess.run(['sudo', 'shutdown', '-h', 'now'])
        except Exception as e:
            print(f"Shutdown error: {e}")
            
    def run(self):
        """Start monitoring"""
        print("Power button monitor started")
        print("Press and hold power button for 3 seconds to shutdown")
        
        try:
            self.monitor_button()
        except KeyboardInterrupt:
            print("\nMonitor stopped")
        finally:
            self.bus.close()

if __name__ == "__main__":
    monitor = PowerButtonMonitor(bus=3, address=0x20)
    monitor.run()
```

#### 3. Systemd Service for Power Button Monitor
```ini
# /etc/systemd/system/dataorb-power-button.service
[Unit]
Description=DataOrb Power Button Monitor
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/pi/dataorb/scripts/power_button_monitor.py
Restart=always
RestartSec=5
User=pi

[Install]
WantedBy=multi-user.target
```

Enable the service:
```bash
sudo systemctl enable dataorb-power-button.service
sudo systemctl start dataorb-power-button.service
```

### Alternative: Simple GPIO Solution (If One Pin Available)

If you can free up a single GPIO pin or use one not fully utilized by HyperPixel:

```bash
# Add to /boot/config.txt
# Use GPIO17 for shutdown (can use different pin)
dtoverlay=gpio-shutdown,gpio_pin=17,active_low=1,gpio_pull=up

# For wake, still need to use RUN header or GPIO3
```

## LED Status Indicator (Optional)

Add an LED to show system status using MCP23017:

```python
# LED on GPA1 of MCP23017
LED_PIN = 0x02

def setup_led(self):
    """Configure LED output"""
    # Set GPA1 as output
    current = self.bus.read_byte_data(self.address, IODIRA)
    self.bus.write_byte_data(self.address, IODIRA, current & ~LED_PIN)
    
def set_led(self, state):
    """Control LED state"""
    current = self.bus.read_byte_data(self.address, GPIOA)
    if state:
        self.bus.write_byte_data(self.address, GPIOA, current | LED_PIN)
    else:
        self.bus.write_byte_data(self.address, GPIOA, current & ~LED_PIN)
        
def blink_led(self, times=3):
    """Blink LED to indicate shutdown"""
    for _ in range(times):
        self.set_led(True)
        time.sleep(0.2)
        self.set_led(False)
        time.sleep(0.2)
```

## Testing the Implementation

1. **Test I2C Communication:**
   ```bash
   # Detect MCP23017 on bus 3
   i2cdetect -y 3
   # Should show device at address 0x20
   ```

2. **Test Button Reading:**
   ```bash
   # Run the monitor script manually
   python3 /home/pi/dataorb/scripts/power_button_monitor.py
   ```

3. **Test Wake Function:**
   - Shutdown the Pi: `sudo shutdown -h now`
   - Wait for activity LED to stop flashing
   - Press the button connected to RUN header
   - Pi should boot

## Power Consumption Notes

- In halt state, Pi Zero W consumes ~30-40mA
- HyperPixel backlight remains on even when Pi is halted
- For true power savings, consider adding a power management board

## Troubleshooting

1. **I2C Device Not Found:**
   - Check wiring connections
   - Ensure alternate I2C bus is enabled in config.txt
   - Verify MCP23017 address jumpers

2. **Button Not Responding:**
   - Check button continuity with multimeter
   - Verify pull-up resistor is enabled
   - Check systemd service logs: `journalctl -u dataorb-power-button`

3. **Wake Not Working:**
   - Ensure RUN header pins are properly soldered
   - Check button connection to RUN pins
   - Verify Pi is in halt state (not powered off)

## Bill of Materials

| Component | Quantity | Purpose | Approx. Cost |
|-----------|----------|---------|--------------|
| MCP23017 DIP-28 | 1 | I2C GPIO Expander | $2.00 |
| Momentary Push Button | 1-2 | Power/Wake control | $1.00 |
| 1N4148 Diode | 1 | GPIO3 isolation (optional) | $0.10 |
| 10kΩ Resistor | 2 | Pull-ups | $0.10 |
| 2-pin Header | 1 | RUN pins connection | $0.20 |
| Hookup Wire | - | Connections | $1.00 |
| **Total** | | | **~$4.40** |

## References

- [HyperPixel Pinout Documentation](https://pinout.xyz/pinout/hyperpixel)
- [MCP23017 Datasheet](https://ww1.microchip.com/downloads/en/devicedoc/20001952c.pdf)
- [Raspberry Pi GPIO Shutdown Overlay](https://github.com/raspberrypi/linux/blob/rpi-5.10.y/arch/arm/boot/dts/overlays/README)
- [I2C on HyperPixel Round Display](https://forums.pimoroni.com/t/i2c-on-the-hypixel-2-1-round-display/24735)