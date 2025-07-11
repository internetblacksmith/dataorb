#!/usr/bin/env python3
"""
Boot update script for PostHog Pi OTA updates
This script runs on boot to check for and apply updates
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config_manager import ConfigManager
from ota_manager import OTAManager

def setup_logging():
    """Setup logging configuration"""
    log_dir = Path('/var/log/posthog-pi')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'ota.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('posthog-pi-ota')

def main():
    """Main boot update function"""
    logger = setup_logging()
    logger.info("Starting PostHog Pi boot update check")
    
    try:
        # Initialize managers
        config_manager = ConfigManager()
        ota_manager = OTAManager(config_manager)
        
        # Perform boot update check
        result = ota_manager.perform_boot_update()
        
        if result.get('skipped'):
            logger.info(f"Boot update skipped: {result.get('reason', 'Unknown')}")
            return 0
        
        if result.get('error'):
            logger.error(f"Boot update failed: {result['error']}")
            return 1
        
        if result.get('no_updates'):
            logger.info("No updates available")
            return 0
        
        if result.get('updates_available') and not result.get('success'):
            logger.info(f"Updates available but not auto-applied: {result.get('commits_behind', 0)} commits behind")
            return 0
        
        if result.get('success'):
            logger.info("Boot update completed successfully")
            logger.info(f"Updated to commit: {result.get('current_commit', 'unknown')}")
            
            # Optionally restart the application service
            config = config_manager.get_section('ota')
            if config.get('restart_after_update', False):
                logger.info("Restarting application service...")
                os.system('sudo systemctl restart posthog-display.service')
            
            return 0
        
        logger.warning("Boot update completed with unknown status")
        return 0
        
    except Exception as e:
        logger.error(f"Boot update script failed: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())