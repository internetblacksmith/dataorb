import os
import subprocess
import json
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
import tempfile
import time


class OTAManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.backup_dir = os.path.join(self.repo_path, ".backups")
        self.log_file = "/var/log/pi-analytics-ota.log"
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)

    def get_status(self) -> Dict[str, Any]:
        """Get current OTA status"""
        config = self.config_manager.get_ota_config()
        
        # Get current Git status
        try:
            current_branch = self._run_command(["git", "branch", "--show-current"], cwd=self.repo_path).strip()
            current_commit = self._run_command(["git", "rev-parse", "HEAD"], cwd=self.repo_path).strip()[:8]
            
            # Check if there are uncommitted changes
            status_output = self._run_command(["git", "status", "--porcelain"], cwd=self.repo_path)
            has_changes = bool(status_output.strip())
            
        except Exception as e:
            current_branch = "unknown"
            current_commit = "unknown"
            has_changes = False
        
        return {
            "enabled": config.get("enabled", True),
            "branch": config.get("branch", "main"),
            "current_branch": current_branch,
            "current_commit": current_commit,
            "has_uncommitted_changes": has_changes,
            "last_update": config.get("last_update"),
            "last_check": config.get("last_check"),
            "auto_pull": config.get("auto_pull", False),
            "check_on_boot": config.get("check_on_boot", True),
        }

    def check_for_updates(self) -> Dict[str, Any]:
        """Check for available updates"""
        try:
            # Fetch latest from remote
            self._run_command(["git", "fetch"], cwd=self.repo_path)
            
            config = self.config_manager.get_ota_config()
            target_branch = config.get("branch", "main")
            
            # Get current and remote commits
            current_commit = self._run_command(
                ["git", "rev-parse", "HEAD"], cwd=self.repo_path
            ).strip()
            
            remote_commit = self._run_command(
                ["git", "rev-parse", f"origin/{target_branch}"], cwd=self.repo_path
            ).strip()
            
            # Get commit count difference
            behind_count = self._run_command(
                ["git", "rev-list", "--count", f"HEAD..origin/{target_branch}"], 
                cwd=self.repo_path
            ).strip()
            
            # Get commit messages for updates
            commit_messages = []
            if int(behind_count) > 0:
                messages = self._run_command(
                    ["git", "log", "--oneline", f"HEAD..origin/{target_branch}"],
                    cwd=self.repo_path
                ).strip()
                if messages:
                    commit_messages = messages.split("\n")
            
            # Update last check time
            self.config_manager.update_ota_config({"last_check": datetime.now().isoformat()})
            
            return {
                "update_available": current_commit != remote_commit,
                "current_commit": current_commit[:8],
                "remote_commit": remote_commit[:8],
                "behind_count": int(behind_count),
                "commits": commit_messages,
                "branch": target_branch,
            }
            
        except Exception as e:
            return {"error": str(e), "update_available": False}

    def perform_update(self, force: bool = False) -> Dict[str, Any]:
        """Perform OTA update"""
        try:
            config = self.config_manager.get_ota_config()
            
            # Check if updates are enabled
            if not config.get("enabled", True) and not force:
                return {"error": "OTA updates are disabled"}
            
            # Check for uncommitted changes
            status_output = self._run_command(["git", "status", "--porcelain"], cwd=self.repo_path)
            if status_output.strip() and not force:
                return {"error": "Uncommitted changes detected. Use force=true to override"}
            
            # Create backup if configured
            if config.get("backup_before_update", True):
                backup_result = self.create_backup()
                if not backup_result.get("success"):
                    return {"error": f"Backup failed: {backup_result.get('error')}"}
            
            target_branch = config.get("branch", "main")
            
            # Stash any local changes
            self._run_command(["git", "stash"], cwd=self.repo_path)
            
            # Checkout target branch
            self._run_command(["git", "checkout", target_branch], cwd=self.repo_path)
            
            # Pull latest changes
            pull_output = self._run_command(
                ["git", "pull", "origin", target_branch], cwd=self.repo_path
            )
            
            # Update last update time
            self.config_manager.update_ota_config({"last_update": datetime.now().isoformat()})
            
            # Log the update
            self._log(f"OTA update completed: {pull_output}")
            
            return {
                "success": True,
                "message": "Update completed successfully",
                "output": pull_output,
                "needs_restart": True,
            }
            
        except Exception as e:
            self._log(f"OTA update failed: {str(e)}")
            return {"error": str(e), "success": False}

    def perform_boot_update(self) -> Dict[str, Any]:
        """Perform update check on boot if configured"""
        config = self.config_manager.get_ota_config()
        
        if not config.get("enabled", True):
            return {"message": "OTA updates disabled"}
        
        if not config.get("check_on_boot", True):
            return {"message": "Boot update check disabled"}
        
        # Check for updates
        update_info = self.check_for_updates()
        
        if update_info.get("update_available") and config.get("auto_pull", False):
            # Perform automatic update
            return self.perform_update(force=False)
        
        return update_info

    def switch_branch(self, branch: str) -> Dict[str, Any]:
        """Switch to a different Git branch"""
        try:
            # Check for uncommitted changes
            status_output = self._run_command(["git", "status", "--porcelain"], cwd=self.repo_path)
            if status_output.strip():
                return {"error": "Uncommitted changes detected. Commit or stash changes first"}
            
            # Fetch latest
            self._run_command(["git", "fetch"], cwd=self.repo_path)
            
            # Switch branch
            self._run_command(["git", "checkout", branch], cwd=self.repo_path)
            
            # Pull latest
            self._run_command(["git", "pull", "origin", branch], cwd=self.repo_path)
            
            # Update configuration
            self.config_manager.update_ota_config({"branch": branch})
            
            return {"success": True, "message": f"Switched to branch: {branch}"}
            
        except Exception as e:
            return {"error": str(e), "success": False}

    def get_available_branches(self) -> Dict[str, Any]:
        """Get list of available branches"""
        try:
            # Fetch latest
            self._run_command(["git", "fetch"], cwd=self.repo_path)
            
            # Get all branches
            branches_output = self._run_command(
                ["git", "branch", "-r"], cwd=self.repo_path
            ).strip()
            
            branches = []
            for line in branches_output.split("\n"):
                branch = line.strip()
                if branch and "origin/" in branch and "HEAD" not in branch:
                    branch_name = branch.replace("origin/", "")
                    branches.append(branch_name)
            
            # Get current branch
            current = self._run_command(
                ["git", "branch", "--show-current"], cwd=self.repo_path
            ).strip()
            
            return {
                "branches": branches,
                "current": current,
            }
            
        except Exception as e:
            return {"error": str(e), "branches": []}

    def create_backup(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a backup of the current installation"""
        try:
            if not name:
                name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = os.path.join(self.backup_dir, name)
            
            # Create backup excluding certain directories
            exclude_dirs = [".git", "node_modules", "__pycache__", "venv", ".backups"]
            
            # Create temporary tar file
            with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
                tar_cmd = ["tar", "-czf", tmp.name, "--exclude=" + " --exclude=".join(exclude_dirs), "."]
                self._run_command(tar_cmd, cwd=self.repo_path)
                
                # Move to backup location
                shutil.move(tmp.name, f"{backup_path}.tar.gz")
            
            # Clean old backups if needed
            self._cleanup_old_backups()
            
            return {"success": True, "backup_name": name, "path": f"{backup_path}.tar.gz"}
            
        except Exception as e:
            return {"error": str(e), "success": False}

    def rollback(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Rollback to a previous backup"""
        try:
            if not backup_name:
                # Get most recent backup
                backups = self.list_backups()
                if not backups.get("backups"):
                    return {"error": "No backups available"}
                backup_name = backups["backups"][0]["name"]
            
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.tar.gz")
            
            if not os.path.exists(backup_path):
                return {"error": f"Backup not found: {backup_name}"}
            
            # Extract backup
            self._run_command(["tar", "-xzf", backup_path], cwd=self.repo_path)
            
            return {"success": True, "message": f"Rolled back to: {backup_name}"}
            
        except Exception as e:
            return {"error": str(e), "success": False}

    def list_backups(self) -> Dict[str, List[Dict[str, Any]]]:
        """List available backups"""
        try:
            backups = []
            
            if os.path.exists(self.backup_dir):
                for file in sorted(os.listdir(self.backup_dir), reverse=True):
                    if file.endswith(".tar.gz"):
                        path = os.path.join(self.backup_dir, file)
                        stat = os.stat(path)
                        backups.append({
                            "name": file.replace(".tar.gz", ""),
                            "size": stat.st_size,
                            "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        })
            
            return {"backups": backups}
            
        except Exception as e:
            return {"error": str(e), "backups": []}

    def get_config(self) -> Dict[str, Any]:
        """Get OTA configuration"""
        return self.config_manager.get_ota_config()

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update OTA configuration"""
        return self.config_manager.update_ota_config(updates)

    def restart_services(self) -> Dict[str, Any]:
        """Restart application services"""
        try:
            # Restart backend service
            self._run_command(["sudo", "systemctl", "restart", "pi-analytics-backend"])
            
            # Restart kiosk if configured
            try:
                self._run_command(["sudo", "systemctl", "restart", "pi-analytics-kiosk"])
            except:
                pass  # Kiosk might not be configured
            
            return {"success": True, "message": "Services restarted"}
            
        except Exception as e:
            return {"error": str(e), "success": False}

    def reboot_system(self, delay: int = 10) -> Dict[str, Any]:
        """Reboot the system"""
        try:
            self._run_command(["sudo", "shutdown", "-r", f"+{delay//60}"])
            return {"success": True, "message": f"System will reboot in {delay} seconds"}
        except Exception as e:
            return {"error": str(e), "success": False}

    def update_cron_schedule(self, schedule: str) -> Dict[str, Any]:
        """Update cron schedule for automatic updates"""
        try:
            # Update config
            self.config_manager.update_ota_config({"update_schedule": schedule})
            
            # Update crontab
            cron_cmd = f'{schedule} cd {self.repo_path} && /usr/bin/python3 {os.path.join(self.repo_path, "scripts", "boot-update.py")}'
            
            # Get current crontab
            try:
                current_cron = self._run_command(["crontab", "-l"])
            except:
                current_cron = ""
            
            # Remove old OTA entries
            new_cron = []
            for line in current_cron.split("\n"):
                if "boot-update.py" not in line:
                    new_cron.append(line)
            
            # Add new entry
            new_cron.append(cron_cmd)
            
            # Update crontab
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
                tmp.write("\n".join(new_cron))
                tmp.flush()
                self._run_command(["crontab", tmp.name])
                os.unlink(tmp.name)
            
            return {"success": True, "schedule": schedule}
            
        except Exception as e:
            return {"error": str(e), "success": False}

    def test_git_connection(self) -> Dict[str, Any]:
        """Test Git connectivity"""
        try:
            output = self._run_command(["git", "ls-remote", "origin"], cwd=self.repo_path)
            return {"success": True, "connected": bool(output)}
        except Exception as e:
            return {"error": str(e), "connected": False}

    def get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            df_output = self._run_command(["df", "-h", "/"])
            lines = df_output.strip().split("\n")
            
            if len(lines) > 1:
                parts = lines[1].split()
                return {
                    "total": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "percent": parts[4],
                }
            
            return {}
            
        except Exception as e:
            return {"error": str(e)}

    def clean_cache(self) -> Dict[str, Any]:
        """Clean temporary files and caches"""
        try:
            cleaned = []
            
            # Clean Python cache
            for root, dirs, files in os.walk(self.repo_path):
                if "__pycache__" in dirs:
                    shutil.rmtree(os.path.join(root, "__pycache__"))
                    cleaned.append("Python cache")
            
            # Clean npm cache if exists
            try:
                self._run_command(["npm", "cache", "clean", "--force"], 
                                cwd=os.path.join(self.repo_path, "frontend"))
                cleaned.append("NPM cache")
            except:
                pass
            
            return {"success": True, "cleaned": cleaned}
            
        except Exception as e:
            return {"error": str(e), "success": False}

    def get_logs(self, lines: int = 100) -> Dict[str, Any]:
        """Get OTA update logs"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, "r") as f:
                    log_lines = f.readlines()
                    return {"logs": log_lines[-lines:]}
            return {"logs": []}
        except Exception as e:
            return {"error": str(e), "logs": []}

    def _run_command(self, cmd: List[str], cwd: str = None) -> str:
        """Run a shell command and return output"""
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return result.stdout

    def _cleanup_old_backups(self):
        """Remove old backups beyond max_backups limit"""
        config = self.config_manager.get_ota_config()
        max_backups = config.get("max_backups", 5)
        
        backups = self.list_backups().get("backups", [])
        if len(backups) > max_backups:
            for backup in backups[max_backups:]:
                try:
                    os.remove(os.path.join(self.backup_dir, f"{backup['name']}.tar.gz"))
                except:
                    pass

    def _log(self, message: str):
        """Log a message"""
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, "a") as f:
                f.write(f"{datetime.now().isoformat()} - {message}\n")
        except:
            pass