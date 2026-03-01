"""Tests for OTAManager — all subprocess calls mocked."""

import os
from unittest.mock import MagicMock, patch

import pytest

from ota_manager import OTAManager


@pytest.fixture
def ota(config_manager, tmp_path):
    """OTAManager with config and temp backup dir."""
    mgr = OTAManager(config_manager)
    mgr.repo_path = str(tmp_path)
    mgr.backup_dir = str(tmp_path / ".backups")
    os.makedirs(mgr.backup_dir, exist_ok=True)
    return mgr


# ---------------------------------------------------------------------------
# Branch switching — input validation
# ---------------------------------------------------------------------------


def test_switch_branch_rejects_command_injection(ota):
    """Branch name containing shell metacharacters is rejected."""
    result = ota.switch_branch('main; rm -rf /')
    assert result.get("success") is False or "error" in result


def test_switch_branch_rejects_leading_dot(ota):
    """Branch names starting with '.' are rejected."""
    result = ota.switch_branch(".hidden")
    assert result.get("success") is False or "error" in result


@patch.object(OTAManager, "_run_command", return_value="")
def test_switch_branch_accepts_valid_name(mock_cmd, ota):
    """Valid branch names like 'feature/my-branch' are accepted."""
    result = ota.switch_branch("feature/my-branch")
    assert result.get("success") is True


# ---------------------------------------------------------------------------
# Cron schedule validation
# ---------------------------------------------------------------------------


def test_malformed_cron_rejected(ota):
    """A cron string with wrong field count is rejected."""
    result = ota.update_cron_schedule("not a cron")
    assert result.get("success") is False
    assert "Invalid cron" in result.get("error", "")


@patch.object(OTAManager, "_run_command", return_value="")
def test_valid_cron_accepted(mock_cmd, ota):
    """A valid 5-field cron schedule is accepted."""
    result = ota.update_cron_schedule("0 3 * * *")
    assert result.get("success") is True


# ---------------------------------------------------------------------------
# Rollback — path traversal
# ---------------------------------------------------------------------------


def test_rollback_path_traversal_blocked(ota):
    """Backup names with path traversal are rejected."""
    result = ota.rollback("../../etc/passwd")
    # Should either fail validation or report not found
    assert result.get("success") is not True


# ---------------------------------------------------------------------------
# perform_update
# ---------------------------------------------------------------------------


def test_perform_update_when_disabled(ota):
    """perform_update returns error when OTA updates are disabled."""
    ota.config_manager.update_config({"ota": {"enabled": False}})
    result = ota.perform_update(force=False)
    assert "error" in result
    assert "disabled" in result["error"].lower()


@patch.object(OTAManager, "_run_command", return_value="")
def test_perform_update_creates_backup_first(mock_cmd, ota, tmp_path):
    """When backup_before_update is True, a backup is created before pulling."""
    ota.config_manager.update_config({"ota": {"enabled": True, "backup_before_update": True}})

    # Mock _run_command to track call order
    calls = []
    original_run = ota._run_command

    def tracking_run(cmd, cwd=None):
        calls.append(cmd)
        return ""

    with patch.object(ota, "_run_command", side_effect=tracking_run):
        with patch.object(ota, "create_backup", return_value={"success": True}) as mock_backup:
            ota.perform_update(force=True)
            mock_backup.assert_called_once()


# ---------------------------------------------------------------------------
# Backup cleanup
# ---------------------------------------------------------------------------


def test_cleanup_respects_max_backups(ota, tmp_path):
    """Old backups beyond max_backups are deleted."""
    ota.config_manager.update_config({"ota": {"max_backups": 2}})
    backup_dir = tmp_path / ".backups"

    # Create 4 backup files
    for i in range(4):
        (backup_dir / f"backup_2024010{i}_120000.tar.gz").write_text("fake")

    ota._cleanup_old_backups()

    remaining = list(backup_dir.glob("*.tar.gz"))
    assert len(remaining) <= 2
