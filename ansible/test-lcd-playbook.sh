#!/bin/bash

# Test the LCD installation playbook on localhost or remote Pi

echo "======================================="
echo "Testing LCD Installation Playbook"
echo "======================================="
echo "This runs the playbook that mirrors test-lcd-install.sh exactly"
echo ""

# Check if we should run locally or remote
if [ "$1" == "local" ]; then
    echo "Running on localhost..."
    cat > /tmp/lcd-hosts << EOF
[pi]
localhost ansible_connection=local
EOF
    ansible-playbook -i /tmp/lcd-hosts lcd-install-playbook.yml --ask-become-pass
else
    echo "Running on remote Pi..."
    echo "Using hosts file: hosts"
    ansible-playbook -i hosts lcd-install-playbook.yml --ask-become-pass
fi

echo ""
echo "======================================="
echo "If successful, REBOOT the Pi and test with:"
echo "  sudo /usr/local/bin/test-hyperpixel.sh"
echo "======================================="