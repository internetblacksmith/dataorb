#!/bin/bash
# PostHog Pi Analytics Dashboard - Installation Script
# For Raspberry Pi Zero W with HyperPixel 2.1 Round Display

set -e

echo "======================================"
echo "  PostHog Pi Analytics Dashboard"
echo "  Installation for Raspberry Pi Zero W"
echo "======================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "❌ This script must be run on a Raspberry Pi!"
    exit 1
fi

# Check for root/sudo
if [ "$EUID" -eq 0 ]; then
    echo "❌ Do not run this script as root/sudo!"
    echo "   Run as regular user: ./install.sh"
    exit 1
fi

# Install Ansible if not present
if ! command -v ansible-playbook >/dev/null 2>&1; then
    echo "📦 Installing Ansible..."
    sudo apt-get update
    sudo apt-get install -y ansible git
fi

# Clone repository if not already cloned
if [ ! -d ~/posthog_pi ]; then
    echo "📥 Cloning PostHog Pi repository..."
    cd ~
    git clone https://github.com/jabawack81/posthog_pi.git
    cd posthog_pi
else
    echo "📂 Using existing repository at ~/posthog_pi"
    cd ~/posthog_pi
    git pull origin main
fi

# Create inventory file
echo "📝 Creating Ansible inventory..."
cat > ansible/inventory.ini << EOF
[pi]
localhost ansible_connection=local ansible_user=$USER
EOF

# Run Ansible playbook
echo "🚀 Running Ansible playbook..."
echo "   This will take 15-30 minutes..."
echo ""

cd ansible
ansible-playbook -i inventory.ini playbook.yml

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Create .env file:"
echo "   cp backend/.env.example backend/.env"
echo "   nano backend/.env"
echo ""
echo "2. Add your PostHog credentials:"
echo "   POSTHOG_API_KEY=phx_xxxxx"
echo "   POSTHOG_PROJECT_ID=xxxxx"
echo ""
echo "3. Reboot to start the dashboard:"
echo "   sudo reboot"
echo ""
echo "📡 WiFi Setup:"
echo "   If no network is detected, the Pi will create:"
echo "   SSID: PostHog-Setup"
echo "   Password: posthog123"
echo "   Connect and visit: 192.168.4.1:5000"
echo ""
echo "🎯 Dashboard will be available at:"
echo "   http://$(hostname -I | cut -d' ' -f1):5000"
echo ""