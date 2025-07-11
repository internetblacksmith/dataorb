#!/bin/bash

# HyperPixel Round Display Diagnostic Script

echo "🔍 HyperPixel Round Display Diagnostics"
echo "======================================="
echo

# Check boot config
echo "📋 Boot Configuration:"
echo "--- /boot/config.txt (HyperPixel sections) ---"
grep -A 10 -B 2 -i hyperpixel /boot/config.txt || echo "❌ No HyperPixel configuration found in /boot/config.txt"
echo

# Check display detection
echo "🖥️ Display Detection:"
echo "--- Connected displays ---"
if command -v xrandr >/dev/null 2>&1; then
    DISPLAY=:0 xrandr 2>/dev/null || echo "Cannot query displays (X11 may not be running)"
else
    echo "xrandr not available"
fi

echo
echo "--- Framebuffer devices ---"
ls -la /dev/fb* 2>/dev/null || echo "No framebuffer devices found"

echo
echo "--- DRM devices ---"
ls -la /dev/dri/* 2>/dev/null || echo "No DRM devices found"
echo

# Check kernel messages
echo "📝 Kernel Messages:"
echo "--- HyperPixel related messages ---"
sudo dmesg | grep -i hyperpixel || echo "No HyperPixel messages in dmesg"

echo
echo "--- Display/DPI related messages ---"
sudo dmesg | grep -i -E "(dpi|lcd|display)" | tail -10 || echo "No display messages found"
echo

# Check X11 status
echo "🖼️ X11 Status:"
if pgrep -x Xorg >/dev/null; then
    echo "✅ Xorg is running"
    echo "X11 processes:"
    ps aux | grep -E "(Xorg|lightdm)" | grep -v grep
else
    echo "❌ Xorg not running"
fi
echo

# Check display environment
echo "🔧 Display Environment:"
echo "DISPLAY variable: ${DISPLAY:-"not set"}"
echo "Current user: $(whoami)"
echo "Current session:"
who am i 2>/dev/null || echo "No session info"
echo

# Check Chrome/Chromium status
echo "🌐 Browser Status:"
if pgrep -f chromium >/dev/null; then
    echo "✅ Chromium is running"
    echo "Chromium processes:"
    ps aux | grep chromium | grep -v grep | head -3
else
    echo "❌ Chromium not running"
fi
echo

# Manual test commands
echo "🛠️ Manual Test Commands:"
echo
echo "1. Test display manually:"
echo "   DISPLAY=:0 xset q"
echo
echo "2. Test basic graphics:"
echo "   DISPLAY=:0 xclock"
echo
echo "3. Test Chromium manually:"
echo "   DISPLAY=:0 chromium-browser http://localhost:5000"
echo
echo "4. Check if display is working:"
echo "   sudo fbi -T 1 /opt/vc/src/hello_pi/hello_triangle/Djenne_128_128.raw"
echo
echo "5. Reconfigure display (if needed):"
echo "   sudo ./config/hyperpixel-setup.sh"
echo "   sudo reboot"
echo

echo "🔄 Common Fixes:"
echo "1. If display is blank:"
echo "   - Check physical connections"
echo "   - Verify /boot/config.txt has HyperPixel settings"
echo "   - Try: sudo systemctl restart lightdm"
echo
echo "2. If wrong orientation:"
echo "   - Edit /boot/config.txt"
echo "   - Change 'dtoverlay=hyperpixel4:rotate=X' (X = 0,90,180,270)"
echo
echo "3. If display shows console but no browser:"
echo "   - Check if PostHog Pi service is running"
echo "   - Check browser autostart in ~/.config/openbox/autostart"