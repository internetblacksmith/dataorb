#!/bin/bash

# Quick deployment script for backend updates
echo "Preparing backend for deployment..."

cd /home/paolo/projects/posthog_pi

# Create a temporary copy without venv and __pycache__
cp -r backend /tmp/backend-deploy
rm -rf /tmp/backend-deploy/venv
rm -rf /tmp/backend-deploy/__pycache__
rm -rf /tmp/backend-deploy/.env

# Create archive
cd /tmp
tar -czf backend-deploy.tar.gz backend-deploy

# Clean up temp directory
rm -rf /tmp/backend-deploy

echo ""
echo "Backend prepared for deployment."
echo ""
echo "To deploy to your Pi, run these commands:"
echo ""
echo "1. Copy the backend archive:"
echo "   scp /tmp/backend-deploy.tar.gz pianalytics@192.168.1.134:~/"
echo ""
echo "2. SSH into the Pi and deploy:"
echo "   ssh pianalytics@192.168.1.134"
echo "   cd /home/pianalytics/pi-analytics-dashboard"
echo "   tar -xzf ~/backend-deploy.tar.gz"
echo "   mv backend backend.old"
echo "   mv backend-deploy backend"
echo "   cp backend.old/.env backend/.env"
echo "   cp -r backend.old/venv backend/"
echo "   rm -rf backend.old"
echo "   rm ~/backend-deploy.tar.gz"
echo "   sudo systemctl restart pi-analytics-backend"
echo ""
echo "3. The configuration page should now be available at:"
echo "   http://192.168.1.134:5000/config"
echo ""
echo "The dashboard will auto-redirect there when PostHog isn't configured!"