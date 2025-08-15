#!/bin/bash

# Quick deployment script for frontend updates
echo "Deploying frontend to Pi..."

# Build frontend
cd frontend
npm run build

# Create archive
tar -czf /tmp/frontend-build.tar.gz build/

echo ""
echo "Frontend built and archived."
echo ""
echo "To deploy to your Pi, run these commands:"
echo ""
echo "1. Copy the archive:"
echo "   scp /tmp/frontend-build.tar.gz pianalytics@192.168.1.134:~/"
echo ""
echo "2. SSH into the Pi and extract:"
echo "   ssh pianalytics@192.168.1.134"
echo "   cd /home/pianalytics/pi-analytics-dashboard/frontend"
echo "   rm -rf build"
echo "   tar -xzf ~/frontend-build.tar.gz"
echo "   rm ~/frontend-build.tar.gz"
echo ""
echo "3. The dashboard will auto-refresh in 30 seconds, or reload manually:"
echo "   sudo killall surf"
echo ""
echo "The dashboard should now auto-redirect to /config when PostHog isn't configured!"