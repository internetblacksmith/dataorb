#!/bin/bash

# PostHog Pi Installation Script
# Run this script on a fresh Raspberry Pi to install everything

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 PostHog Pi Installation Script${NC}"
echo "This will install PostHog Pi on your Raspberry Pi"
echo

# Configuration
REPO_URL="https://github.com/jabawack81/posthog_pi.git"
CURRENT_USER=$(whoami)
INSTALL_DIR="$HOME/posthog_pi"

echo -e "${GREEN}Installing PostHog Pi for user: $CURRENT_USER${NC}"

echo -e "${YELLOW}📦 Step 1: Installing system dependencies...${NC}"
sudo apt update
sudo apt install -y \
    git \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    chromium-browser \
    xorg \
    openbox \
    lightdm \
    curl \
    wget

echo -e "${YELLOW}📥 Step 2: Cloning repository...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo "Directory exists, updating..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo -e "${YELLOW}🐍 Step 3: Setting up Python environment...${NC}"
cd "$INSTALL_DIR/backend"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo -e "${YELLOW}📱 Step 4: Building React frontend...${NC}"
cd "$INSTALL_DIR/frontend"

# Check available memory and enable swap if needed
echo "Checking system memory..."
AVAILABLE_MEM=$(free -m | awk 'NR==2{print $7}')
echo "Available memory: ${AVAILABLE_MEM}MB"

if [ "$AVAILABLE_MEM" -lt 200 ]; then
    echo -e "${YELLOW}Low memory detected, enabling temporary swap file...${NC}"
    sudo dd if=/dev/zero of=/tmp/swapfile bs=1M count=512 2>/dev/null || true
    sudo mkswap /tmp/swapfile 2>/dev/null || true
    sudo swapon /tmp/swapfile 2>/dev/null || true
fi

# Install dependencies with reduced parallelism for low-memory systems
echo "Installing Node.js dependencies with memory optimizations..."
npm install --no-audit --no-fund --maxsockets 1

# Set Node.js memory options for Raspberry Pi
echo "Building React with memory optimizations for Raspberry Pi..."
export NODE_OPTIONS="--max_old_space_size=512"
export GENERATE_SOURCEMAP=false

# Try building with reduced memory usage
if ! npm run build; then
    echo -e "${YELLOW}Build failed, trying with more aggressive memory limits...${NC}"
    export NODE_OPTIONS="--max_old_space_size=256"
    
    if ! npm run build; then
        echo -e "${RED}❌ React build failed even with memory optimizations${NC}"
        echo -e "${YELLOW}💡 Troubleshooting suggestions:${NC}"
        echo "1. Ensure you have at least 512MB free RAM"
        echo "2. Close other applications to free memory"
        echo "3. Consider adding permanent swap space:"
        echo "   sudo dphys-swapfile setup"
        echo "   sudo dphys-swapfile swapon"
        echo "4. Or try building on a machine with more RAM and copying the build folder"
        echo
        echo -e "${YELLOW}You can also skip the build and use the pre-built files by running:${NC}"
        echo "   cd $INSTALL_DIR && git checkout origin/main -- frontend/build"
        exit 1
    fi
fi

# Clean up temporary swap file if we created one
if [ -f /tmp/swapfile ]; then
    echo "Cleaning up temporary swap file..."
    sudo swapoff /tmp/swapfile 2>/dev/null || true
    sudo rm -f /tmp/swapfile 2>/dev/null || true
fi

echo -e "${YELLOW}⚙️ Step 5: Creating configuration files...${NC}"
cd "$INSTALL_DIR/backend"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file - you'll need to configure PostHog credentials"
fi

echo -e "${YELLOW}🔧 Step 6: Installing OTA service...${NC}"
cd "$INSTALL_DIR"
sudo ./scripts/install-ota-service.sh

echo -e "${YELLOW}🖥️ Step 7: Setting up display service...${NC}"
# Create systemd service for the app
sudo tee /etc/systemd/system/posthog-display.service > /dev/null <<EOF
[Unit]
Description=PostHog Pi Display Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR/backend
Environment=DISPLAY=:0
Environment=HOME=$HOME
ExecStart=$INSTALL_DIR/backend/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable posthog-display.service

echo -e "${YELLOW}🎮 Step 8: Setting up kiosk mode...${NC}"
# Create kiosk startup script
mkdir -p $HOME/.config/openbox
tee $HOME/.config/openbox/autostart > /dev/null <<EOF
# Wait for the display service to start
sleep 10

# Start Chromium in kiosk mode
chromium-browser \\
    --kiosk \\
    --no-sandbox \\
    --disable-infobars \\
    --disable-session-crashed-bubble \\
    --disable-component-extensions-with-background-pages \\
    --disable-background-networking \\
    --disable-background-timer-throttling \\
    --disable-backgrounding-occluded-windows \\
    --disable-renderer-backgrounding \\
    --disable-features=TranslateUI \\
    --disable-ipc-flooding-protection \\
    --window-size=480,480 \\
    --window-position=0,0 \\
    http://localhost:5000
EOF

# Set up auto-login
sudo tee /etc/lightdm/lightdm.conf > /dev/null <<EOF
[Seat:*]
autologin-user=$CURRENT_USER
autologin-user-timeout=0
user-session=openbox
EOF

echo -e "${YELLOW}🔄 Step 9: Configuring boot options...${NC}"
# Enable auto-login
sudo systemctl enable lightdm

echo -e "${GREEN}✅ Installation Complete!${NC}"
echo
echo "🎯 Next Steps:"
echo "1. Configure PostHog credentials:"
echo "   nano $INSTALL_DIR/backend/.env"
echo
echo "2. Add your PostHog API key and project ID"
echo
echo "3. Start the services:"
echo "   sudo systemctl start posthog-display.service"
echo
echo "4. Access the dashboard:"
echo "   http://raspberry-pi-ip:5000"
echo
echo "5. Access configuration:"
echo "   http://raspberry-pi-ip:5000/config"
echo
echo "6. Reboot to start kiosk mode:"
echo "   sudo reboot"
echo
echo -e "${YELLOW}📝 Configuration Notes:${NC}"
echo "• The app will auto-start on boot"
echo "• Kiosk mode will launch automatically"
echo "• Use Ctrl+Shift+C to access config in kiosk mode"
echo "• OTA updates are configured and ready"
echo
echo -e "${GREEN}🎉 PostHog Pi is ready to use!${NC}"