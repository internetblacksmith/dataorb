#!/bin/bash
# Deploy frontend build to Raspberry Pi
# Builds locally and transfers to Pi to avoid memory issues

set -e

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Get Pi host from command line or use default
PI_HOST=${1:-pianalytics@pianalytics.local}

echo "======================================="
echo "Frontend Deployment to Raspberry Pi"
echo "======================================="
echo ""
echo "Target: $PI_HOST"
echo "Project root: $PROJECT_ROOT"
echo ""

# Build frontend locally
echo "Building frontend locally..."
cd "$PROJECT_ROOT/frontend"
npm run build

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo "Build successful!"

# Create a tarball of the build directory
echo "Creating deployment package..."
tar -czf build.tar.gz build/

# Transfer to Pi
echo "Transferring to Pi..."
scp build.tar.gz $PI_HOST:/tmp/

# Extract on Pi and move to correct location
echo "Installing on Pi..."
ssh $PI_HOST << 'ENDSSH'
    cd /home/pianalytics/pi-analytics-dashboard/frontend
    
    # Backup existing build if it exists
    if [ -d build ]; then
        rm -rf build.backup
        mv build build.backup
    fi
    
    # Extract new build
    tar -xzf /tmp/build.tar.gz
    rm /tmp/build.tar.gz
    
    # Restart the backend service to pick up new frontend
    sudo systemctl restart pi-analytics-backend || true
    
    # Reload display
    pkill -HUP surf || true
    
    echo "Deployment complete!"
ENDSSH

# Clean up local tarball
rm build.tar.gz

echo ""
echo "======================================="
echo "Deployment successful!"
echo "======================================="
echo ""
echo "The frontend has been deployed to $PI_HOST"
echo "The display should reload automatically"