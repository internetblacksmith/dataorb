#!/bin/bash

# Pi Analytics Dashboard - Ansible Deployment Script
# This script simplifies the deployment process

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default verbosity
VERBOSE=""

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -vv|--very-verbose)
            VERBOSE="-vv"
            shift
            ;;
        -vvv|--debug)
            VERBOSE="-vvv"
            shift
            ;;
        -vvvv|--connection-debug)
            VERBOSE="-vvvv"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose             Show task output (recommended)"
            echo "  -vv, --very-verbose       Show task output + results"
            echo "  -vvv, --debug             Show task output + results + task arguments"
            echo "  -vvvv, --connection-debug Full debug including SSH connection details"
            echo "  -h, --help                Show this help message"
            echo ""
            echo "Verbosity Levels Explained:"
            echo "  Normal:     Shows task names only"
            echo "  -v:         Shows stdout/stderr from tasks"
            echo "  -vv:        Adds task results and module arguments"
            echo "  -vvv:       Adds full task information before execution"
            echo "  -vvvv:      Adds SSH connection debugging"
            echo ""
            echo "Example:"
            echo "  $0 --verbose    # Recommended for first-time deployment"
            echo "  $0              # Interactive mode (will ask for verbosity)"
            exit 0
            ;;
    esac
done

echo "========================================="
echo "Pi Analytics Dashboard Deployment"
echo "========================================="
echo ""

# Suggest verbose mode if not enabled
if [ -z "$VERBOSE" ]; then
    echo -e "${YELLOW}ℹ️  This deployment includes dependency installation which can take 10-30 minutes${NC}"
    echo -e "${YELLOW}   Verbose output helps track progress during long operations${NC}"
    echo ""
    echo "Select verbosity level:"
    echo -e "${GREEN}0)${NC} Normal output (quiet)"
    echo -e "${GREEN}1)${NC} Verbose (-v) - ${BLUE}Shows task output${NC} [Recommended]"
    echo -e "${GREEN}2)${NC} Very Verbose (-vv) - Shows task output + results"
    echo -e "${GREEN}3)${NC} Debug (-vvv) - Shows task output + results + task arguments"
    echo -e "${GREEN}4)${NC} Connection Debug (-vvvv) - Full debug including connection details"
    echo ""
    read -p "Select verbosity level [0-4] (default: 1): " verbosity_choice
    
    # Default to option 1 (verbose) if just Enter is pressed
    verbosity_choice=${verbosity_choice:-1}
    
    case $verbosity_choice in
        0)
            VERBOSE=""
            echo -e "${GREEN}✓ Using normal output (quiet)${NC}"
            ;;
        1)
            VERBOSE="-v"
            echo -e "${GREEN}✓ Using verbose output (-v)${NC}"
            ;;
        2)
            VERBOSE="-vv"
            echo -e "${GREEN}✓ Using very verbose output (-vv)${NC}"
            ;;
        3)
            VERBOSE="-vvv"
            echo -e "${GREEN}✓ Using debug output (-vvv)${NC}"
            ;;
        4)
            VERBOSE="-vvvv"
            echo -e "${GREEN}✓ Using connection debug output (-vvvv)${NC}"
            ;;
        *)
            VERBOSE="-v"
            echo -e "${YELLOW}Invalid choice. Using recommended verbose output (-v)${NC}"
            ;;
    esac
    echo ""
fi

# Check if ansible is installed
if ! command -v ansible &> /dev/null; then
    echo -e "${YELLOW}Ansible not found. Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install ansible
    else
        # Linux
        sudo apt-get update
        sudo apt-get install -y ansible
    fi
fi

# Check for inventory file
INVENTORY_CREATED=false
if [ ! -f inventory.ini ]; then
    echo -e "${YELLOW}Creating inventory.ini from template...${NC}"
    
    if [ ! -f inventory.ini.example ]; then
        echo -e "${RED}inventory.ini.example not found!${NC}"
        echo "The template file is missing. Please check your repository."
        exit 1
    fi
    
    # Copy the example file
    cp inventory.ini.example inventory.ini
    echo -e "${GREEN}✓ Created inventory.ini from template${NC}"
    INVENTORY_CREATED=true
fi

# Check if configuration is needed (new file or has example values)
NEEDS_EDIT=false
EDIT_REASON=""

if [ "$INVENTORY_CREATED" = true ]; then
    NEEDS_EDIT=true
    EDIT_REASON="New inventory file created"
elif grep -q "posthogpi.local\|192.168.1.100\|CHANGE_ME\|#raspberrypi.local\|#192.168.1.100" inventory.ini 2>/dev/null; then
    NEEDS_EDIT=true
    EDIT_REASON="Inventory contains example/default values"
fi

# Single edit prompt if needed
if [ "$NEEDS_EDIT" = true ]; then
    echo ""
    echo -e "${YELLOW}⚠️  $EDIT_REASON${NC}"
    echo ""
    echo "Please configure your Raspberry Pi connection details:"
    echo "  • Replace the IP address or hostname"
    echo "  • Update the username if not 'pi'"
    echo "  • Set your SSH password or key path"
    echo "  • Uncomment ONE of the example lines"
    echo ""
    
    # Show current content - only actual hosts, not vars
    echo "Current inventory content:"
    echo "---"
    awk '
        /^\[pi\]$/ { in_pi=1; print; next }
        /^\[/ { in_pi=0 }
        in_pi && !/^#/ && !/^$/ && /ansible_/ { print "  " $0 }
    ' inventory.ini || echo "(No active configuration found)"
    echo "---"
    echo ""
    
    read -p "Open editor to configure? [Y/n]: " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        ${EDITOR:-nano} inventory.ini
    else
        # Show full inventory configuration and ask for confirmation
        echo ""
        echo -e "${YELLOW}Current inventory configuration:${NC}"
        echo "========================================="
        
        # Show the [pi] section
        echo -e "${BLUE}[pi] section:${NC}"
        awk '
            /^\[pi\]$/ { in_pi=1; print "  " $0; next }
            /^\[pi:vars\]$/ { in_pi=0 }
            /^\[/ && !/^\[pi/ { in_pi=0 }
            in_pi && !/^$/ { print "  " $0 }
        ' inventory.ini
        
        echo ""
        echo -e "${BLUE}[pi:vars] section:${NC}"
        awk '
            /^\[pi:vars\]$/ { in_vars=1; print "  " $0; next }
            /^\[/ && !/^\[pi:vars\]$/ { in_vars=0 }
            in_vars && !/^$/ { print "  " $0 }
        ' inventory.ini
        
        echo "========================================="
        echo ""
        
        # Extract active configuration for summary
        ACTIVE_HOST=$(awk '
            /^\[pi\]$/ { in_pi=1; next }
            /^\[/ { in_pi=0 }
            in_pi && !/^#/ && !/^$/ && /ansible_/ { print $1; exit }
        ' inventory.ini)
        
        PI_MODEL=$(awk -F= '/^pi_model=/ {gsub(/[ \t]/, "", $2); print $2}' inventory.ini)
        DISPLAY_TYPE=$(awk -F= '/^display_type=/ {gsub(/[ \t]/, "", $2); print $2}' inventory.ini)
        
        if [ -n "$ACTIVE_HOST" ]; then
            echo -e "${GREEN}Active configuration detected:${NC}"
            echo "  • Host: $ACTIVE_HOST"
            echo "  • Pi Model: ${PI_MODEL:-not set}"
            echo "  • Display Type: ${DISPLAY_TYPE:-not set}"
        else
            echo -e "${RED}No active host configuration found!${NC}"
            echo "All host lines are commented out."
        fi
        
        echo ""
        echo -e "${YELLOW}⚠️  Warning: Connection may fail without proper configuration${NC}"
        echo ""
        read -p "Are you sure you want to continue with this configuration? [y/N]: " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Returning to edit option..."
            echo ""
            read -p "Open editor to configure inventory? [Y/n]: " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                ${EDITOR:-nano} inventory.ini
            else
                echo "Exiting without changes."
                exit 1
            fi
        fi
    fi
fi

# Install required collections
echo -e "${GREEN}Installing Ansible requirements...${NC}"
ansible-galaxy collection install -r requirements.yml --force

# Skip PostHog credentials - will be configured on first boot
echo -e "${GREEN}PostHog credentials will be configured on first boot via web interface${NC}"

# Run deployment
echo ""
echo -e "${GREEN}Starting deployment...${NC}"
echo ""

# Get the Pi host(s) from inventory - only from the [pi] section, not [pi:vars]
# This extracts lines between [pi] and the next section that aren't comments or empty
# and contain ansible configuration (ansible_user, ansible_ssh_pass, etc)
PI_HOSTS=$(awk '
    /^\[pi\]$/ { in_pi=1; next }
    /^\[/ { in_pi=0 }
    in_pi && !/^#/ && !/^$/ && /ansible_/ { print $1 }
' inventory.ini)

# If no hosts found, show error
if [ -z "$PI_HOSTS" ]; then
    echo -e "${RED}No hosts found in inventory.ini!${NC}"
    echo "Please uncomment and configure at least one host in the [pi] section"
    exit 1
fi

PI_COUNT=$(echo "$PI_HOSTS" | wc -l)

if [ $PI_COUNT -eq 1 ]; then
    echo "Target host: $PI_HOSTS"
else
    echo "Target hosts ($PI_COUNT Pis):"
    echo "$PI_HOSTS" | while read host; do
        echo "  • $host"
    done
fi

# Handle SSH known_hosts for all hosts
echo ""
echo "Checking SSH host keys..."
echo "DEBUG: PI_HOSTS = '$PI_HOSTS'"

# Temporarily disable exit on error for SSH key handling
set +e

# Save PI_HOSTS to temporary file to avoid subshell issues
TEMP_HOSTS_FILE="/tmp/ansible_hosts_$$"
echo "DEBUG: Creating temp file: $TEMP_HOSTS_FILE"
echo "$PI_HOSTS" > "$TEMP_HOSTS_FILE"
echo "DEBUG: Temp file contents:"
cat "$TEMP_HOSTS_FILE"

# Process each host from temp file
echo "DEBUG: Starting host processing loop..."
while IFS= read -r PI_HOST; do
    # Extract just the hostname/IP from the inventory line
    CLEAN_HOST=$(echo $PI_HOST | sed 's/ansible_.*//g' | tr -d ' ')
    
    echo "DEBUG: Processing PI_HOST='$PI_HOST'"
    
    if [ -z "$CLEAN_HOST" ]; then
        echo "DEBUG: CLEAN_HOST is empty, skipping"
        continue
    fi
    
    echo ""
    echo "Processing: $CLEAN_HOST"
    
    # Get the username from this specific line or use default
    ANSIBLE_USER=$(echo $PI_HOST | grep -o 'ansible_user=[^ ]*' | cut -d= -f2 || echo "pi")

# Check if host is already in known_hosts
if ssh-keygen -F "$CLEAN_HOST" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Host $CLEAN_HOST found in known_hosts${NC}"
    echo "Checking if key is valid..."
    
    # Get the new host key
    NEW_KEY=$(ssh-keyscan -t ed25519,ecdsa,rsa "$CLEAN_HOST" 2>/dev/null)
    
    if [ -z "$NEW_KEY" ]; then
        echo -e "${RED}Could not retrieve host key from $CLEAN_HOST${NC}"
        echo "Please check that the Pi is online and SSH is enabled"
        exit 1
    fi
    
    # Try to verify if the key matches by attempting a simple keyscan comparison
    # If ssh-keyscan succeeds but we can't connect, the key likely changed
    echo "$NEW_KEY" | ssh-keygen -lf - > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        # We got a valid key, now check if it matches what we have
        TEMP_KNOWN="/tmp/ansible_temp_known_hosts_$$"
        ssh-keyscan -H "$CLEAN_HOST" 2>/dev/null > "$TEMP_KNOWN"
        
        # Check if we can verify against existing known_hosts
        if ! ssh-keygen -F "$CLEAN_HOST" -f ~/.ssh/known_hosts | grep -q "$(ssh-keygen -lf $TEMP_KNOWN 2>/dev/null | awk '{print $2}')"; then
            echo -e "${YELLOW}⚠️  Host key has changed (Pi was likely reflashed)${NC}"
            echo ""
            echo "This is normal if you:"
            echo "  • Reflashed the SD card"
            echo "  • Reinstalled the OS"
            echo "  • Changed the Pi hardware"
            echo ""
            read -p "Remove old key and add new one? [Y/n]: " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                # Remove the old key
                ssh-keygen -R "$CLEAN_HOST" 2>/dev/null
                echo -e "${GREEN}✓ Old host key removed${NC}"
                
                # Add the new key
                cat "$TEMP_KNOWN" >> ~/.ssh/known_hosts
                echo -e "${GREEN}✓ New host key added${NC}"
            else
                echo -e "${RED}Cannot continue without updating host key${NC}"
                echo "To manually fix, run:"
                echo -e "${BLUE}  ssh-keygen -R $CLEAN_HOST${NC}"
                echo -e "${BLUE}  ssh-keyscan -H $CLEAN_HOST >> ~/.ssh/known_hosts${NC}"
                rm -f "$TEMP_KNOWN"
                exit 1
            fi
        else
            echo -e "${GREEN}✓ Host key verified${NC}"
        fi
        rm -f "$TEMP_KNOWN"
    fi
else
    echo -e "${YELLOW}⚠️  Host $CLEAN_HOST not in known_hosts${NC}"
    echo "Adding host key automatically (first-time connection)..."
    
    # Use ssh-keyscan to add the host key automatically
    ssh-keyscan -H "$CLEAN_HOST" 2>/dev/null >> ~/.ssh/known_hosts
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Host key added to known_hosts${NC}"
    else
        echo -e "${YELLOW}Could not automatically add host key${NC}"
        echo "You may need to manually SSH once to accept the host key:"
        echo -e "${BLUE}  ssh $ANSIBLE_USER@$CLEAN_HOST${NC}"
        echo ""
        read -p "Do you want to continue anyway? [y/N]: " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi
done < "$TEMP_HOSTS_FILE"

# Clean up temp file
rm -f "$TEMP_HOSTS_FILE"

# Re-enable exit on error
set -e

# Set Ansible to accept new host keys automatically for this session
export ANSIBLE_HOST_KEY_CHECKING=False

# Check connection first
echo ""
echo "Testing connection to Raspberry Pi..."
if ansible -i inventory.ini pi -m ping $VERBOSE; then
    echo -e "${GREEN}✓ Connection successful!${NC}"
else
    echo -e "${RED}✗ Failed to connect to Raspberry Pi!${NC}"
    echo "Please check:"
    echo "  1. Raspberry Pi is powered on and connected to network"
    echo "  2. inventory.ini has correct IP/hostname"
    echo "  3. SSH credentials are correct"
    echo "  4. SSH is enabled on the Pi (raspi-config)"
    exit 1
fi

# Run playbook
echo ""
case "$VERBOSE" in
    "")
        echo "Running deployment playbook (normal output)..."
        echo -e "${YELLOW}Tip: Run with --verbose or select option 2 to see progress${NC}"
        ;;
    "-v")
        echo -e "${BLUE}Running deployment with verbose output...${NC}"
        echo -e "${YELLOW}You'll see output from each task as it runs${NC}"
        ;;
    "-vv")
        echo -e "${BLUE}Running deployment with very verbose output...${NC}"
        echo -e "${YELLOW}You'll see task output and results${NC}"
        ;;
    "-vvv")
        echo -e "${BLUE}Running deployment with debug output...${NC}"
        echo -e "${YELLOW}You'll see full task details and arguments${NC}"
        ;;
    "-vvvv")
        echo -e "${BLUE}Running deployment with connection debug output...${NC}"
        echo -e "${YELLOW}You'll see SSH connection details and full debugging${NC}"
        ;;
esac
echo -e "${YELLOW}Note: Installation may take 20-30 minutes on Pi Zero W${NC}"
echo ""
ansible-playbook -i inventory.ini playbook.yml $VERBOSE

echo ""
echo "========================================="
echo -e "${GREEN}Deployment complete!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Reboot the Raspberry Pi: ansible -i inventory.ini pi -m reboot --become"
echo "2. Wait for the Pi to restart (about 1 minute)"
echo "3. The display should show the analytics dashboard"
echo "4. Access web interface at: http://<pi-ip>:5000"
echo ""