# Pi Analytics Dashboard - Ansible Deployment

Automated deployment solution for Pi Analytics Dashboard on Raspberry Pi Zero W with HyperPixel Round display.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/jabawack81/pi_analytics_dashboard.git
cd pi_analytics_dashboard/ansible

# Run deployment with verbose output (recommended)
./deploy.sh --verbose

# Or run quietly (default)
./deploy.sh
```

## Prerequisites

### On Control Machine (your computer)
- Ansible 2.9+ (installed automatically by deploy.sh)
- SSH access to Raspberry Pi
- Git
- Optional: `sshpass` for password-based authentication with rsync
  - Install with: `sudo apt-get install sshpass` (Ubuntu/Debian)
  - Or use SSH keys instead (recommended)

### On Raspberry Pi
- Raspberry Pi OS (Bookworm or Buster)
- Network connectivity
- SSH enabled

## Configuration

### 1. Inventory Setup

The deployment script will automatically create `inventory.ini` from the template on first run.

If you need to manually create it:
```bash
cp inventory.ini.example inventory.ini
# Edit with your Pi's details
nano inventory.ini
```

Example configurations:
```ini
[pi]
# Single Pi setup
raspberrypi.local ansible_user=pi ansible_ssh_pass=yourpassword

# Or using IP address
192.168.1.100 ansible_user=pi ansible_ssh_pass=yourpassword

# Or using SSH key (recommended)
192.168.1.100 ansible_user=pi ansible_ssh_private_key_file=~/.ssh/id_rsa

# Multiple Pis - Deploy to all simultaneously!
pi-office.local ansible_user=pi ansible_ssh_pass=password1
pi-lobby.local ansible_user=pi ansible_ssh_pass=password2
pi-conference.local ansible_user=pi ansible_ssh_pass=password3
```

**Multi-Pi Deployment**: Ansible can deploy to multiple Pis in parallel! Just add multiple lines to the `[pi]` section. Each Pi will get its own installation and can be configured individually after deployment.

**Note:** `inventory.ini` is gitignored to keep your credentials private.

### 2. PostHog Credentials

PostHog credentials are configured on first boot via the device's web interface:
1. After deployment, the Pi will create a WiFi access point
2. Connect to "PiAnalytics-Setup" network (password: setupme123)
3. Open browser to configure PostHog API credentials
4. Device will save settings and connect to your WiFi

### 3. Display Configuration

Set display type in `inventory.ini`:
```ini
[pi:vars]
display_type=hyperpixel_round  # Options: hyperpixel_round, hyperpixel_square, hdmi
```

### 4. WiFi Configuration (Optional)

Add WiFi credentials to `inventory.ini`:
```ini
[pi:vars]
wifi_ssid=YourWiFiNetwork
wifi_password=YourWiFiPassword
wifi_country=US
```

## Deployment Methods

### Method 1: Using Deploy Script (Recommended)

```bash
# With verbose output (shows progress during long operations)
./deploy.sh --verbose

# Or let the script ask you
./deploy.sh

# For debugging issues
./deploy.sh --debug
```

Features:
- Automatic Ansible installation
- Interactive verbosity selection
- Connection testing
- Progress indication for long tasks
- Time estimates for each phase

**Deployment Time Estimates** (Pi Zero W):
- System packages: 5-10 minutes
- Python dependencies: 5-10 minutes  
- Node dependencies: 3-5 minutes
- Frontend build: 2-3 minutes
- **Total: ~20-30 minutes**

### Method 2: Manual Ansible Commands

```bash
# Install requirements
ansible-galaxy install -r requirements.yml

# Test connection
ansible -i inventory.ini pi -m ping

# Run playbook
ansible-playbook -i inventory.ini playbook.yml --ask-vault-pass
```

### Method 3: Specific Tags

Deploy only specific components:

```bash
# System preparation only
ansible-playbook -i inventory.ini playbook.yml --tags system

# Display configuration only
ansible-playbook -i inventory.ini playbook.yml --tags display

# Application deployment only
ansible-playbook -i inventory.ini playbook.yml --tags app

# Services setup only
ansible-playbook -i inventory.ini playbook.yml --tags services
```

## Playbook Structure

The deployment consists of four phases:

### Phase 1: System Preparation
- Updates package lists
- Installs system dependencies
- Configures locale and timezone
- Sets up WiFi (if configured)

### Phase 2: Display Configuration
- Detects OS version (Bookworm/Buster)
- Configures HyperPixel display
- Sets up framebuffer settings
- Enables SPI interface

### Phase 3: Application Deployment
- Clones repository
- Installs Python dependencies
- Builds React frontend
- Configures PostHog credentials
- Sets up device configuration

### Phase 4: Service Setup
- Creates systemd services
- Configures auto-start on boot
- Sets up kiosk mode
- Enables OTA updates

## Files and Templates

### Templates
- `posthog-display.service.j2` - Main application service
- `posthog-pi-ota.service.j2` - OTA update service
- `env.j2` - PostHog credentials
- `device_config.json.j2` - Device configuration
- `start-kiosk.sh.j2` - Kiosk startup script
- `wpa_supplicant.conf.j2` - WiFi configuration

### Configuration Files
- `inventory.ini` - Target host configuration
- `group_vars/all.yml` - Global variables
- `group_vars/vault.yml` - Encrypted credentials (created during setup)
- `requirements.yml` - Ansible dependencies

## Variables

### Required Variables
- `pi_model` - Raspberry Pi model: pi_zero_w, pi_zero_2w, pi3, pi4, or pi5
- `display_type` - Display type: hyperpixel_round, waveshare_34_hdmi, or hdmi
- `vault_posthog_api_key` - PostHog API key (encrypted) - set after deployment via web UI
- `vault_posthog_project_id` - PostHog project ID (encrypted) - set after deployment via web UI

### Optional Variables
- `display_width` - Display width in pixels (default: 480)
- `display_height` - Display height in pixels (default: 480)
- `wifi_ssid` - WiFi network name
- `wifi_password` - WiFi password
- `wifi_country` - WiFi country code (default: US)
- `ota_enabled` - Enable OTA updates (default: true)
- `ota_branch` - Git branch for updates (default: main)

## Post-Deployment

After successful deployment:

1. **Reboot Raspberry Pi**:
   ```bash
   ansible -i inventory.ini pi -m reboot --become
   ```

2. **First Boot Configuration**:
   - Pi creates WiFi AP: "PiAnalytics-Setup" (password: setupme123)
   - Connect to this network from your phone/laptop
   - Open browser to `http://192.168.4.1:5000`
   - Configure PostHog credentials and WiFi settings
   - Pi will restart and connect to your network

3. **After Configuration**:
   - Display: Shows analytics dashboard
   - Web UI: `http://<pi-ip>:5000`
   - Config: `http://<pi-ip>:5000/config` or press Ctrl+Shift+C on display

## Troubleshooting

### Connection Issues

The deploy script automatically handles SSH host keys for first-time connections. If you still have issues:

```bash
# Test SSH manually
ssh pi@raspberrypi.local

# Enable SSH on Pi
# (Connect keyboard/monitor to Pi)
sudo systemctl enable ssh
sudo systemctl start ssh

# Clear old host key if Pi was reimaged
ssh-keygen -R raspberrypi.local
ssh-keygen -R 192.168.1.x  # Use your Pi's IP
```

### Display Not Working
```bash
# Check display service
ansible -i inventory.ini pi -m command --args "systemctl status posthog-display" --become

# Check display configuration
ansible -i inventory.ini pi -m command --args "cat /boot/firmware/config.txt" --become
```

### Application Errors
```bash
# View application logs
ansible -i inventory.ini pi -m command --args "journalctl -u posthog-display -f" --become

# Check Python environment
ansible -i inventory.ini pi -m command --args "ls -la /home/pi/pi_analytics_dashboard/backend/venv" --become
```

### Credential Issues
```bash
# Re-encrypt credentials
ansible-vault encrypt_string 'new-api-key' --ask-vault-pass

# Edit vault file
ansible-vault edit group_vars/vault.yml
```

## Security Considerations

1. **Encrypted Credentials**: All sensitive data is encrypted using Ansible Vault
2. **SSH Keys**: Prefer SSH keys over passwords for authentication
3. **Network Security**: Use WPA2/WPA3 for WiFi connections
4. **Updates**: Keep system packages and application updated

## Advanced Usage

### Custom Variables
Create `host_vars/<hostname>.yml` for host-specific configuration:
```yaml
---
display_type: hdmi
display_width: 1920
display_height: 1080
```

### Multiple Pis
Add multiple Pis to inventory:
```ini
[pi]
pi1.local ansible_user=pi
pi2.local ansible_user=pi
pi3.local ansible_user=pi
```

Deploy to all:
```bash
ansible-playbook -i inventory.ini playbook.yml
```

### Rollback
```bash
# Stop services
ansible -i inventory.ini pi -m systemd --args "name=posthog-display state=stopped" --become

# Remove application
ansible -i inventory.ini pi -m file --args "path=/home/pi/pi_analytics_dashboard state=absent" --become

# Remove services
ansible -i inventory.ini pi -m file --args "path=/etc/systemd/system/posthog-display.service state=absent" --become
```

## Support

- [GitHub Issues](https://github.com/jabawack81/pi_analytics_dashboard/issues)
- [Project Documentation](https://jabawack81.github.io/pi_analytics_dashboard/)
- [PostHog Documentation](https://posthog.com/docs)
- [HyperPixel Documentation](https://github.com/pimoroni/hyperpixel2r)