import os
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from config_manager import ConfigManager

class OTAManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.repo_path = os.path.dirname(os.path.abspath(__file__ + "/../"))
        self.git_command = "git"
        
    def get_current_branch(self) -> str:
        """Get the current git branch"""
        try:
            result = subprocess.run(
                [self.git_command, "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def get_current_commit(self) -> str:
        """Get the current git commit hash"""
        try:
            result = subprocess.run(
                [self.git_command, "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def get_remote_branches(self) -> List[str]:
        """Get list of remote branches"""
        try:
            # Fetch remote branches
            subprocess.run(
                [self.git_command, "fetch", "--all"],
                cwd=self.repo_path,
                capture_output=True
            )
            
            result = subprocess.run(
                [self.git_command, "branch", "-r"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                branches = []
                for line in result.stdout.strip().split('\n'):
                    branch = line.strip()
                    if branch and not branch.startswith('origin/HEAD'):
                        # Remove 'origin/' prefix
                        branch_name = branch.replace('origin/', '')
                        branches.append(branch_name)
                return sorted(list(set(branches)))
            return ["main", "dev", "canary"]
        except Exception:
            return ["main", "dev", "canary"]
    
    def get_status(self) -> Dict[str, Any]:
        """Get OTA status information"""
        config = self.config_manager.get_section("ota")
        
        return {
            "enabled": config.get("enabled", True),
            "current_branch": self.get_current_branch(),
            "current_commit": self.get_current_commit(),
            "target_branch": config.get("branch", "main"),
            "available_branches": self.get_remote_branches(),
            "auto_pull": config.get("auto_pull", True),
            "check_on_boot": config.get("check_on_boot", True),
            "last_update": config.get("last_update"),
            "last_check": config.get("last_check"),
            "repo_path": self.repo_path
        }
    
    def check_for_updates(self) -> Dict[str, Any]:
        """Check if updates are available"""
        try:
            # Update last check time
            self.config_manager.update_section("ota", {
                "last_check": datetime.now().isoformat()
            })
            
            # Fetch latest changes
            result = subprocess.run(
                [self.git_command, "fetch", "origin"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {
                    "updates_available": False,
                    "error": f"Failed to fetch updates: {result.stderr}"
                }
            
            # Check if remote branch is ahead
            config = self.config_manager.get_section("ota")
            target_branch = config.get("branch", "main")
            
            result = subprocess.run(
                [self.git_command, "rev-list", "--count", f"HEAD..origin/{target_branch}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                commits_behind = int(result.stdout.strip())
                return {
                    "updates_available": commits_behind > 0,
                    "commits_behind": commits_behind,
                    "target_branch": target_branch
                }
            else:
                return {
                    "updates_available": False,
                    "error": f"Failed to check commits: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "updates_available": False,
                "error": f"Exception checking for updates: {str(e)}"
            }
    
    def switch_branch(self, branch: str) -> Dict[str, Any]:
        """Switch to a different branch"""
        try:
            # Fetch latest changes
            subprocess.run(
                [self.git_command, "fetch", "origin"],
                cwd=self.repo_path,
                capture_output=True
            )
            
            # Switch to branch
            result = subprocess.run(
                [self.git_command, "checkout", f"origin/{branch}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to switch to branch {branch}: {result.stderr}"
                }
            
            # Update config
            self.config_manager.update_section("ota", {
                "branch": branch,
                "last_update": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": f"Successfully switched to branch {branch}",
                "current_branch": self.get_current_branch(),
                "current_commit": self.get_current_commit()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception switching branch: {str(e)}"
            }
    
    def create_backup(self) -> Dict[str, Any]:
        """Create a backup of the current state"""
        try:
            backup_tag = f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Create a local tag as backup
            result = subprocess.run(
                [self.git_command, "tag", backup_tag],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to create backup tag: {result.stderr}"
                }
            
            return {
                "success": True,
                "backup_tag": backup_tag,
                "message": f"Created backup tag: {backup_tag}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception creating backup: {str(e)}"
            }
    
    def rollback_to_backup(self, backup_tag: str) -> Dict[str, Any]:
        """Rollback to a specific backup tag"""
        try:
            # Reset to backup tag
            result = subprocess.run(
                [self.git_command, "reset", "--hard", backup_tag],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to rollback to backup: {result.stderr}"
                }
            
            # Update config
            self.config_manager.update_section("ota", {
                "last_update": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": f"Successfully rolled back to backup: {backup_tag}",
                "current_commit": self.get_current_commit()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception during rollback: {str(e)}"
            }
    
    def get_backups(self) -> List[str]:
        """Get list of available backup tags"""
        try:
            result = subprocess.run(
                [self.git_command, "tag", "-l", "backup-*"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return sorted(result.stdout.strip().split('\n'), reverse=True)
            return []
            
        except Exception:
            return []
    
    def pull_updates(self) -> Dict[str, Any]:
        """Pull latest updates from current branch with backup"""
        try:
            config = self.config_manager.get_section("ota")
            target_branch = config.get("branch", "main")
            
            # Create backup before update
            backup_result = self.create_backup()
            if not backup_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to create backup: {backup_result.get('error')}"
                }
            
            backup_tag = backup_result["backup_tag"]
            
            # Fetch and pull
            subprocess.run(
                [self.git_command, "fetch", "origin"],
                cwd=self.repo_path,
                capture_output=True
            )
            
            result = subprocess.run(
                [self.git_command, "pull", "origin", target_branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Rollback on failure
                rollback_result = self.rollback_to_backup(backup_tag)
                return {
                    "success": False,
                    "error": f"Failed to pull updates: {result.stderr}",
                    "rollback": rollback_result.get("success", False)
                }
            
            # Update config
            self.config_manager.update_section("ota", {
                "last_update": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": "Successfully pulled updates",
                "current_commit": self.get_current_commit(),
                "output": result.stdout,
                "backup_tag": backup_tag
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception pulling updates: {str(e)}"
            }
    
    def reset_to_remote(self, branch: str) -> Dict[str, Any]:
        """Reset local branch to match remote (hard reset)"""
        try:
            # Fetch latest changes
            subprocess.run(
                [self.git_command, "fetch", "origin"],
                cwd=self.repo_path,
                capture_output=True
            )
            
            # Hard reset to remote branch
            result = subprocess.run(
                [self.git_command, "reset", "--hard", f"origin/{branch}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to reset to remote branch: {result.stderr}"
                }
            
            # Update config
            self.config_manager.update_section("ota", {
                "branch": branch,
                "last_update": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": f"Successfully reset to remote branch {branch}",
                "current_commit": self.get_current_commit()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception resetting to remote: {str(e)}"
            }
    
    def perform_boot_update(self) -> Dict[str, Any]:
        """Perform OTA update on boot if enabled"""
        config = self.config_manager.get_section("ota")
        
        if not config.get("enabled", True) or not config.get("check_on_boot", True):
            return {"skipped": True, "reason": "OTA disabled or check_on_boot disabled"}
        
        # Check for updates
        update_check = self.check_for_updates()
        
        if update_check.get("error"):
            return {"error": update_check["error"]}
        
        if not update_check.get("updates_available", False):
            return {"no_updates": True}
        
        # Auto-pull if enabled
        if config.get("auto_pull", True):
            return self.pull_updates()
        else:
            return {
                "updates_available": True,
                "commits_behind": update_check.get("commits_behind", 0),
                "message": "Updates available but auto-pull disabled"
            }