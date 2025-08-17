#!/usr/bin/env python3
"""
Power button monitor for DataOrb with HyperPixel display
Monitors button press via I2C (MCP23017) and triggers safe shutdown
Can also be used with direct GPIO if available
"""

import time
import subprocess
import sys
import os
import signal
import logging
from typing import Optional

# Try to import GPIO libraries
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    
# Try to import I2C library
try:
    import smbus
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False

# MCP23017 Registers
IODIRA = 0x00  # I/O direction register A
IODIRB = 0x01  # I/O direction register B
GPPUA = 0x0C   # Pull-up register A
GPPUB = 0x0D   # Pull-up register B
GPIOA = 0x12   # GPIO register A
GPIOB = 0x13   # GPIO register B
OLATA = 0x14   # Output latch register A
OLATB = 0x15   # Output latch register B

# Configuration
DEFAULT_I2C_BUS = 3  # Alternate I2C bus on HyperPixel
DEFAULT_MCP_ADDRESS = 0x20
DEFAULT_GPIO_PIN = 17  # If using direct GPIO instead of I2C
SHUTDOWN_HOLD_TIME = 3  # Seconds to hold for shutdown
DEBOUNCE_TIME = 0.05  # Button debounce time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PowerButton')


class PowerButtonMonitor:
    """Monitor power button and handle shutdown"""
    
    def __init__(self, use_i2c: bool = True, i2c_bus: int = DEFAULT_I2C_BUS, 
                 mcp_address: int = DEFAULT_MCP_ADDRESS, gpio_pin: int = DEFAULT_GPIO_PIN):
        """
        Initialize power button monitor
        
        Args:
            use_i2c: Use I2C/MCP23017 if True, direct GPIO if False
            i2c_bus: I2C bus number
            mcp_address: MCP23017 I2C address
            gpio_pin: GPIO pin number if not using I2C
        """
        self.use_i2c = use_i2c and I2C_AVAILABLE
        self.running = True
        self.button_pressed_time: Optional[float] = None
        self.last_state = False
        
        if self.use_i2c:
            try:
                self.bus = smbus.SMBus(i2c_bus)
                self.mcp_address = mcp_address
                self.setup_mcp23017()
                logger.info(f"Initialized I2C button on bus {i2c_bus}, address 0x{mcp_address:02x}")
            except Exception as e:
                logger.error(f"Failed to initialize I2C: {e}")
                if GPIO_AVAILABLE:
                    logger.info("Falling back to GPIO mode")
                    self.use_i2c = False
                else:
                    raise
                    
        if not self.use_i2c and GPIO_AVAILABLE:
            self.gpio_pin = gpio_pin
            self.setup_gpio()
            logger.info(f"Initialized GPIO button on pin {gpio_pin}")
        elif not self.use_i2c and not GPIO_AVAILABLE:
            logger.error("Neither I2C nor GPIO available!")
            sys.exit(1)
            
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal")
        self.cleanup()
        sys.exit(0)
        
    def setup_mcp23017(self):
        """Configure MCP23017 for button input with LED output"""
        # Set GPA0 as input (button), GPA1 as output (LED)
        self.bus.write_byte_data(self.mcp_address, IODIRA, 0x01)
        # Enable pull-up on GPA0 (button)
        self.bus.write_byte_data(self.mcp_address, GPPUA, 0x01)
        # Turn on LED to indicate ready
        self.set_led(True)
        
    def setup_gpio(self):
        """Configure direct GPIO for button input"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
    def read_button(self) -> bool:
        """
        Read button state
        
        Returns:
            True if button is pressed, False otherwise
        """
        try:
            if self.use_i2c:
                # Read GPIOA register from MCP23017
                state = self.bus.read_byte_data(self.mcp_address, GPIOA)
                # Button pressed when GPA0 is LOW (active low with pull-up)
                return (state & 0x01) == 0
            else:
                # Read GPIO pin (active low with pull-up)
                return GPIO.input(self.gpio_pin) == 0
        except Exception as e:
            logger.error(f"Error reading button: {e}")
            return False
            
    def set_led(self, state: bool):
        """
        Control status LED (if using MCP23017)
        
        Args:
            state: True for on, False for off
        """
        if not self.use_i2c:
            return
            
        try:
            current = self.bus.read_byte_data(self.mcp_address, GPIOA)
            if state:
                # Set GPA1 high (LED on)
                self.bus.write_byte_data(self.mcp_address, GPIOA, current | 0x02)
            else:
                # Set GPA1 low (LED off)
                self.bus.write_byte_data(self.mcp_address, GPIOA, current & ~0x02)
        except Exception as e:
            logger.error(f"Error setting LED: {e}")
            
    def blink_led(self, times: int = 3, interval: float = 0.2):
        """
        Blink LED to indicate action
        
        Args:
            times: Number of blinks
            interval: Time between blinks
        """
        for _ in range(times):
            self.set_led(True)
            time.sleep(interval)
            self.set_led(False)
            time.sleep(interval)
            
    def save_state(self):
        """Save application state before shutdown"""
        try:
            # Create a marker file to indicate clean shutdown
            with open('/tmp/dataorb_clean_shutdown', 'w') as f:
                f.write(str(time.time()))
            logger.info("Saved shutdown state")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            
    def shutdown(self):
        """Perform safe shutdown"""
        logger.info("Initiating safe shutdown...")
        
        # Blink LED to indicate shutdown
        if self.use_i2c:
            self.blink_led(5, 0.1)
            
        # Save application state
        self.save_state()
        
        # Stop DataOrb service if running
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', 'dataorb-display'], 
                         check=False, timeout=5)
            logger.info("Stopped DataOrb display service")
        except Exception as e:
            logger.warning(f"Could not stop display service: {e}")
            
        # Perform system shutdown
        try:
            logger.info("Executing system shutdown...")
            subprocess.run(['sudo', 'shutdown', '-h', 'now'])
        except Exception as e:
            logger.error(f"Shutdown command failed: {e}")
            # Try alternative shutdown method
            try:
                subprocess.run(['sudo', 'halt'])
            except:
                logger.critical("All shutdown methods failed!")
                
    def monitor_button(self):
        """Main monitoring loop"""
        logger.info("Power button monitor started")
        logger.info(f"Hold button for {SHUTDOWN_HOLD_TIME} seconds to shutdown")
        
        while self.running:
            try:
                button_pressed = self.read_button()
                
                # Debounce
                if button_pressed != self.last_state:
                    time.sleep(DEBOUNCE_TIME)
                    button_pressed = self.read_button()
                    
                if button_pressed and not self.last_state:
                    # Button just pressed
                    self.button_pressed_time = time.time()
                    logger.info("Power button pressed...")
                    if self.use_i2c:
                        self.set_led(False)  # Turn off LED during press
                        
                elif button_pressed and self.button_pressed_time:
                    # Button held
                    hold_time = time.time() - self.button_pressed_time
                    if hold_time >= SHUTDOWN_HOLD_TIME:
                        logger.info(f"Button held for {hold_time:.1f}s - shutting down...")
                        self.shutdown()
                        self.running = False
                        
                elif not button_pressed and self.last_state:
                    # Button released
                    if self.button_pressed_time:
                        hold_time = time.time() - self.button_pressed_time
                        if hold_time < SHUTDOWN_HOLD_TIME:
                            logger.info(f"Button released after {hold_time:.1f}s - ignored")
                        self.button_pressed_time = None
                        if self.use_i2c:
                            self.set_led(True)  # Turn LED back on
                            
                self.last_state = button_pressed
                time.sleep(0.05)  # Small delay to reduce CPU usage
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(1)  # Wait before retrying
                
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up...")
        
        if self.use_i2c:
            try:
                self.set_led(False)  # Turn off LED
                self.bus.close()
            except:
                pass
        elif GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except:
                pass
                
        self.running = False
        
    def run(self):
        """Start the monitor"""
        try:
            self.monitor_button()
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='DataOrb Power Button Monitor')
    parser.add_argument('--gpio', action='store_true', 
                       help='Use GPIO instead of I2C')
    parser.add_argument('--gpio-pin', type=int, default=DEFAULT_GPIO_PIN,
                       help=f'GPIO pin number (default: {DEFAULT_GPIO_PIN})')
    parser.add_argument('--i2c-bus', type=int, default=DEFAULT_I2C_BUS,
                       help=f'I2C bus number (default: {DEFAULT_I2C_BUS})')
    parser.add_argument('--mcp-address', type=lambda x: int(x, 0), 
                       default=DEFAULT_MCP_ADDRESS,
                       help=f'MCP23017 I2C address (default: 0x{DEFAULT_MCP_ADDRESS:02x})')
    parser.add_argument('--hold-time', type=float, default=SHUTDOWN_HOLD_TIME,
                       help=f'Hold time for shutdown in seconds (default: {SHUTDOWN_HOLD_TIME})')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Update global config
    global SHUTDOWN_HOLD_TIME
    SHUTDOWN_HOLD_TIME = args.hold_time
    
    # Create and run monitor
    try:
        monitor = PowerButtonMonitor(
            use_i2c=not args.gpio,
            i2c_bus=args.i2c_bus,
            mcp_address=args.mcp_address,
            gpio_pin=args.gpio_pin
        )
        monitor.run()
    except Exception as e:
        logger.error(f"Failed to start monitor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()